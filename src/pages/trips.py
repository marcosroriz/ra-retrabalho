from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import dash
from services.trips_event import TripsEventService

dash.register_page(__name__, path='/trips', icon="material-symbols:home-outline")

# Instanciando o serviço que manipula os dados
trips_db = TripsEventService()

# Layout da página /trips
layout = html.Div([
    html.H1("Viagens por Dia", style={'text-align': 'center', 'margin-bottom': '30px', 'color': '#4A90E2'}),

    # Seção de Seleção do Veículo e Data
    html.Div([
        html.Label("Selecione a Frota:", style={'font-weight': 'bold', 'font-size': '16px', 'margin-bottom': '8px'}),
        dcc.Input(
            id="vehicle-input",
            placeholder="Digite o ID da frota (EX: 50432)",
            type="text",  # Tipo de input para texto
            style={
                'width': '300px',
                'padding': '10px',
                'border-radius': '8px',
                'border': '1px solid #ccc',
                'box-shadow': '0 2px 5px rgba(0, 0, 0, 0.1)',
                'background-color': '#fff',
                'margin': '10px auto'
            }
        ),

        html.Label("Selecione o Dia:", style={'font-weight': 'bold', 'font-size': '16px', 'margin-top': '20px', 'margin-bottom': '8px'}),
        dcc.Dropdown(
            id="date-dropdown",
            options=[],  # Será preenchido com as datas disponíveis para o veículo selecionado
            placeholder="Selecione uma data",
            style={
                'width': '320px',
                'padding': '12px 20px',
                'border-radius': '12px',
                'border': '1px solid #b3b3b3',
                'box-shadow': '0 4px 12px rgba(0, 0, 0, 0.15)',
                'background-color': '#f9f9f9',
                'color': '#333',
                'font-size': '16px',
                'font-weight': '500',
                'transition': 'all 0.3s ease',
                'margin': '10px auto',
                'outline': 'none',
            }
        ),
    ], style={'margin-bottom': '30px', 'text-align': 'center'}),

    # Seção do gráfico de temperatura
    html.Div([
        html.H3("Temperatura", style={'text-align': 'center'}),
        dcc.Graph(id="temp-graph"),
    ], style={'padding': '10px', 'background-color': '#f9f9f9', 'border-radius': '8px', 'box-shadow': '0 2px 5px rgba(0, 0, 0, 0.1)'}),

], style={'padding': '20px', 'font-family': 'Arial, sans-serif'})

# Callback para gerar o gráfico de temperatura e as opções de datas com base na seleção do veículo
@dash.callback(
    [Output("temp-graph", "figure"),
     Output("date-dropdown", "options")],
    [Input("vehicle-input", "value"),
     Input("date-dropdown", "value")],
)
def update_graph(vehicle, date):
    if not vehicle:
        return {}, []  # Se nenhum veículo for selecionado, retorna gráfico vazio e sem opções de data

    # Consultar os dias disponíveis para o veículo selecionado
    available_dates = trips_db.trips_of_vehicle(frota_id=vehicle)
    print(available_dates)

    # Atualizar o Dropdown de datas com as datas disponíveis
    date_options = [{"label": d, "value": d} for d in available_dates['Dia']]

    if not date:
        # Se nenhuma data for selecionada, exibir o primeiro dia disponível
        date = available_dates[0] if available_dates else None

    # Se uma data for selecionada, obter os dados das viagens para esse veículo e data
    if date:
        trips_data = trips_db.get_trips_data(vehicle, date)

        # Gerando o gráfico de temperatura com base nos dados
        fig_temp = px.line(trips_data, x="hour", y="temperature", title="Temperatura")

        return fig_temp, date_options
    else:
        return {}, date_options
