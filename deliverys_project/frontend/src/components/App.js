import React from "react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Table from './Table'

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      data: [],
      loaded: false,
      placeholder: "Loading"
    };
  }

  componentDidMount() {
    fetch("api/deliverys")
      .then(response => {
        if (response.status > 400) {
          return this.setState(() => {
            return { placeholder: "Something went wrong!" };
          });
        }
        return response.json();
      })
      .then(data => {
        this.setState(() => {
          return {
            data,
            loaded: true
          };
        });
      });
  }

  render() {
    this.state.data.map((object) => {
      if (object["amount_dol"].split('.')[1] == "00"){
        object["amount_dol"] = object["amount_dol"].split('.')[0]
      }
      if (object["amount_rub"].split('.')[1] == "00"){
        object["amount_rub"] = object["amount_rub"].split('.')[0]
      }
      if (object["amount_dol"].slice(-1) != '$'){
        object["amount_dol"] += ' $'
      }
      if (object["amount_rub"].slice(-1) != 'р'){
        object["amount_rub"] += ' р'
      }
      object["delivery"] = object["delivery"].split('-').reverse().join('.')
    })
    return (
      <ul>
        <div className="App">
          <Table data={this.state.data}/>
        </div>
      </ul>
    );
  }
}

export default App;

const rootElement = document.getElementById("app");
const root = createRoot(rootElement);

root.render(
  <StrictMode>
    <App />
  </StrictMode>
);