import React from 'react';
import {BootstrapTable, 
       TableHeaderColumn} from 'react-bootstrap-table';
import '../../node_modules/react-bootstrap-table/css/react-bootstrap-table.css'
 
 
class Table extends React.Component {
  render() {
    return (
      <div>
        <BootstrapTable data={this.props.data}>
          <TableHeaderColumn isKey dataField='id' width="10%">
            ID
          </TableHeaderColumn>
          <TableHeaderColumn dataField='order_id' width="10%">
            Номер заказа
          </TableHeaderColumn>
          <TableHeaderColumn dataField='amount_dol' width="20%">
            Стоимость($)
          </TableHeaderColumn>
          <TableHeaderColumn dataField='amount_rub' width="20%">
            Стоимость(руб)
          </TableHeaderColumn>
          <TableHeaderColumn dataField='delivery' width="20%">
            Дата поставки
          </TableHeaderColumn>
        </BootstrapTable>
      </div>
    );
  }
}
 
export default Table;