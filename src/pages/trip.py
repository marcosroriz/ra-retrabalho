import random
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import dash

from modules.trips.trips_service import TripsService
from modules.trips.callbacks import update_components

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

