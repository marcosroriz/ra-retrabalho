
from dash import Input, Output, callback
import plotly.graph_objects as go
import pandas as pd
import dash

from .trips_service import TripsService
from .functions import generate_timeline

db = TripsService()

# Callback para atualizar os componentes
@callback(
    [
        Output('vehicle-dropdown', 'options'),
        Output('event-filter', 'options'),
        Output('timeline-graph', 'figure'),
    ],
    [
        Input('vehicle-dropdown', 'value'),
        Input('date-picker', 'date'),
        Input('event-filter', 'value')
    ]
)
def update_components(selected_vehicle, selected_date, selected_events):
    # Consultar os veículos
    try:
        vehicles = db.get_vehicles()
    except Exception as e:
        vehicles = []
        print(f"Erro ao buscar veículos: {e}")

    dropdown_options = [{'label': vehicle, 'value': vehicle} for vehicle in vehicles]
    
    if not selected_vehicle:
        selected_vehicle = "50334"

    # Caso nenhum veículo ou data seja selecionado, retornar apenas os veículos no dropdown
    if not selected_vehicle or not selected_date:
        return dropdown_options, [], go.Figure()

    # Consultar eventos para o veículo selecionado
    try:
        events = db.get_events(selected_vehicle)
        events['data_evento'] = pd.to_datetime(events['data_evento'], format='%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Erro ao buscar eventos: {e}")
        return dropdown_options, [], go.Figure()

    # Filtrar apenas os eventos do dia selecionado
    selected_date = pd.to_datetime(selected_date).date()
    events = events[events['data_evento'].dt.date == selected_date]

    # Caso não haja eventos, retornar o dropdown e um gráfico vazio
    if events.empty:
        return dropdown_options, [], go.Figure()

    # Atualizar opções de eventos no filtro
    event_options = [{'label': event, 'value': event} for event in events['evento'].unique()]

    # Filtrar eventos selecionados
    if selected_events:
        events = events[events['evento'].isin(selected_events)]

    # Caso os eventos filtrados estejam vazios, retornar um gráfico vazio
    if events.empty:
        return dropdown_options, event_options, go.Figure()

    # Gerar timeline
    fig = generate_timeline(events.to_dict(orient='records'))
    return dropdown_options, event_options, fig