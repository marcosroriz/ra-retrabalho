from dash import Dash, dcc, html, Input, Output, callback
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
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
    html.Div(id='output-container-date-picker-range')
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
        return "Nenhum dado encontrado"
    
    return  [html.P(f"{trip}") for trip in response]
