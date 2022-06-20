from django.db import models

class Поставки(models.Model):
    id = models.IntegerField(db_column="id", primary_key=True)
    order_id = models.IntegerField(db_column="номер_заказа")
    amount_dol = models.DecimalField(decimal_places=2, max_digits=10, db_column="стоимость_$")
    amount_rub = models.DecimalField(decimal_places=2, max_digits=10, db_column="стоимость_руб")
    delivery = models.DateField(db_column="срок_поставки")

    class Meta:
        db_table = "Поставки"
