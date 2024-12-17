from dash import Dash, dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from datetime import date
import dash

from services.trips_event import TripsEventService

dash.register_page(__name__, path='/trips', icon="material-symbols:home-outline")

# Instanciando o serviço que manipula os dados
trips_db = TripsEventService()

layout = html.Div([
    dcc.DatePickerRange(
        id='my-date-picker-range',
        min_date_allowed=date(2024, 1, 1),
        max_date_allowed=date.today(),
        initial_visible_month=date.today(),
        end_date=date.today()
    ),
    html.Div(
        id='output-container-date-picker-range',
        className="mt-3",
        style={"max-height": "200px", "overflow-y": "auto", "max-width":"200px" }  # Adicionando rolagem
    ),
    html.Div(id="selected-trip", className="mt-3"),  # Para exibir o valor do botão clicado
])


@callback(
    Output('output-container-date-picker-range', 'children'),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date'))
def update_output(start_date, end_date):
    response = trips_db.trips_in_day(
        start_date=start_date,
        end_date=end_date
    )
    
    if not response:
        return dbc.Alert("Nenhum dado encontrado", color="warning")
    
    # Criação de botões, cada um com um `id` único
    buttons = [
        dbc.Button(f"{trip}", id={'type': 'trip-button', 'index': idx}, color="primary", className="m-1") 
        for idx, trip in enumerate(response)
    ]
    return dbc.ButtonGroup(buttons, vertical=True)