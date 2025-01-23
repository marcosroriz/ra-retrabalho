import random
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import dash

from modules.trips.trips_service import TripsService
from modules.trips.functions import generate_timeline


db = TripsService()

dash.register_page(__name__, path='/timeline', icon="material-symbols:timeline")


# Layout da página
layout = html.Div([
    # Dropdown de Veículo
    dcc.Dropdown(
        id='vehicle-dropdown',
        placeholder="Selecione um veículo",
        className="mb-3",
        value=None,
        style={
            'border-radius': '8px',  # Borda arredondada
            'background-color': '#f0f0f0',  # Cor de fundo suave
            'padding': '3px',
            'width': '100%',  # Ocupa toda a largura disponível
            'font-size': '16px'
        }
    ),
    
    # DatePicker para data
    dcc.DatePickerSingle(
        id='date-picker',
        placeholder="Selecione uma data",
        className="mb-3",
        display_format="DD/MM/YYYY",
        date=datetime.now().replace(day=8).strftime('%Y-%m-%d'),
        style={
            'border-radius': '8px',
            'background-color': '#f0f0f0',
            'padding': '10px',
            'width': '100%',
        }
    ),
    
    # Dropdown para filtro de eventos
    dcc.Dropdown(
        id='event-filter',
        options=[],  # As opções serão carregadas dinamicamente
        value=[],    # Nenhum evento selecionado por padrão
        multi=True,  # Permite selecionar múltiplos eventos
        placeholder="Selecione eventos",
        className="mb-3",
        style={
            'border-radius': '8px',
            'background-color': '#f0f0f0',
            'padding': '10px',
            'width': '100%',
        }
    ),
    
    # Título da Timeline
    html.Div(
        html.H2("Timeline de Eventos", style={'textAlign': 'center', 'marginTop': '20px', 'color': '#333'}),
        style={'marginBottom': '20px'}
    ),
    
    # Gráfico centralizado
    html.Div(
        
        dcc.Graph(id='timeline-graph'),
        style={
            'display': 'flex',
            'justify-content': 'center',
            'align-items': 'center',
            'height': '87vh',  # Ajustar altura para acomodar o título
            'width': '100%',
            'background-color': '#fafafa',  # Fundo suave
            'border-radius': '15px',  # Borda arredondada no gráfico
        }
    )
])


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