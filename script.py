import time
import re
import httplib2
import datetime
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import psycopg2
from requests import get
import xmltodict
import telebot
from json import load

TYPES_WRAPPER = {
                'date': "'-'",
                }

def value_wrapper(column, value, columns):
    if TYPES_WRAPPER.get(columns.get(column, None)) is None:
        return value
    wrap = TYPES_WRAPPER.get(columns.get(column, None)).split('-')
    wrap.insert(1, value)
    return "".join(wrap)

def check_deliverys(bot, data, yesterday, telegram_id):
    for id in data.keys():
        if datetime.date(*list(map(int, reversed(data[id][2].split("."))))) == yesterday:
            bot.send_message(telegram_id, f"Срок поставки прошел\nid: {id}\nНомер заказа: {data[id][0]}\nСтоимость($): {data[id][1]}\nСрок поставки: {data[id][2]}")

class DolRub:

    def __init__(self, date):
        while True:
            try:
                cbr_date = "/".join(reversed(str(date).split('-')))
                rate_str = xmltodict.parse(get(f'http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={cbr_date}&date_req2={cbr_date}&VAL_NM_RQ=R01235').text)['ValCurs']['Record']['Value']
                break
            except KeyError:
                date -= datetime.timedelta(days=1)
        self.__rate = float('.'.join(rate_str.split(',')))

    def converte(self, dol):
        return str(round(dol*self.__rate, 2))

class PostgreSQL:

    def __init__(self, db_name, db_user, db_password, db_host, db_port):
        self.__connection = psycopg2.connect(
                database=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
            )
        print("Connection to PostgreSQL DB successful")

    def SELECT(self, table, columns="*"):
        cursor = self.__connection.cursor()
        if columns == "*":
            cursor.execute(f"SELECT * FROM {table}")
        else:
            cursor.execute(f"SELECT {', '.join(columns)} FROM {table}")
        return cursor.fetchall()

    def UPDATE(self, table, column, pkey, value, columns):
        cursor = self.__connection.cursor()
        cursor.execute(f"UPDATE {table} SET {column} = {value_wrapper(column, value, columns)} WHERE id = {pkey}")
        self.__connection.commit()

    def INSERT(self, table, columns, columns_types, values):
        cursor = self.__connection.cursor()
        cursor.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join([value_wrapper(columns[index], value, columns_types) for index, value in enumerate(values)])})")
        self.__connection.commit()

    def DELETE(self, table, pkey):
        cursor = self.__connection.cursor()
        cursor.execute(f"DELETE FROM {table} WHERE id = {pkey}")
        self.__connection.commit()

class GoogleSheet:

    def __init__(self, sheatId, creden_file, data):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(creden_file, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
        self.__service = build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API
        self.__sheatId = sheatId
        self.__limit_count = 100
        self.__data = {}
        if len(data) != 0:
            for row in data:
                if row[2] * 100 % 100 == 0:
                    round = str(int(row[2]))
                else:
                    round = str(row[2])
                self.__data[str(row[0])] = [str(row[1]), round, ".".join(reversed(str(row[4]).split('-')))]

    @property
    def data(self):
        return self.__data

    def update_data(self, db, rate, columns, table_name):
        results = self.__service.spreadsheets().values().batchGet(spreadsheetId = self.__sheatId, 
                                            ranges = [f"A2:D{self.__limit_count}"], 
                                            valueRenderOption = 'FORMATTED_VALUE',  
                                            dateTimeRenderOption = 'FORMATTED_STRING').execute()
        values = {}
        for i in results['valueRanges'][0]['values']:
            if self.__is_valid(i):
                values[i[0]] = (i[1], ".".join(i[2].split(',')), i[3]) # Если встречаются дубликаты первичных ключей, используются данные, записанные в последнюю очередь
        values_ids = set(values.keys())
        data_ids = set(self.__data.keys())
        insert_ids = values_ids - data_ids
        delete_ids = data_ids - values_ids
        if insert_ids != set(): # Проверка на вставку в базу данных
            for id in insert_ids:
                db.INSERT(table_name, list(columns.keys()), (id, values[id][0], values[id][1], rate.converte(float(values[id][1])), columns, values[id][2]))
                self.__data[id] = [values[id][0], values[id][1], values[id][2]]
        if delete_ids != set(): # Проверка на удаление из бд (Если данные невалидны, они удаляются из бд)
            for id in delete_ids:
                db.DELETE(table_name, id)
                del self.__data[id]
        for value_id in values.keys(): # Проверка на изменение строки в бд
            for i in range(3):
                if values[value_id][i] != self.__data[value_id][i]:
                    if i == 0:
                        db.UPDATE(table_name, 'номер_заказа', value_id, values[value_id][0], columns)
                    elif i == 1:
                        db.UPDATE(table_name, "стоимость_$", value_id, values[value_id][1], columns)
                        db.UPDATE(table_name, "стоимость_руб", value_id, rate.converte(float(values[value_id][1])), columns)
                    elif i == 2:
                        db.UPDATE(table_name, "срок_поставки", value_id, values[value_id][2], columns)
                    self.__data[value_id][i] = values[value_id][i]
        self.__update_limit()

    def __is_valid(self, row):
        if len(row) != 4:
            return False
        for i in range(2):
            if not re.match(r'\d+', row[i]):
                return False
        if not re.match(r'\d+\.?\d*', row[2]):
            return False
        try:
            datetime.datetime.strptime(row[3], '%d.%m.%Y').date()
        except ValueError:
            return False
        return True

    def __update_limit(self):
        if abs(self.__limit_count - len(self.__data.keys())) < 200:
            self.__limit_count = len(self.__data.keys()) + 100

def main():
    with open('config.json') as file:
        conf = load(file)
        bot = telebot.TeleBot(conf.get("tg_bot_token"))
        db = PostgreSQL(conf.get("db_name"), conf.get("db_user"), conf.get("db_password"), conf.get("db_ip"), conf.get("db_port")) 
        COLUMNS = conf.get("columns")
        TABLE_NAME = conf.get("table_name")
        sheet = GoogleSheet(conf.get("google_sheet_id"), conf.get("google_cred_file"), db.SELECT(TABLE_NAME))
        RECEIVER_ID = int(conf.get("tg_receiver_id"))
    today = datetime.date.today()
    rate = DolRub(today)
    while True:
        sheet.update_data(db, rate, COLUMNS, TABLE_NAME)
        time.sleep(3)
        if today < datetime.date.today():
            check_deliverys(bot, sheet.data, today, RECEIVER_ID)
            today = datetime.date.today()
            rate = DolRub(today)

if __name__ == "__main__":
    main()