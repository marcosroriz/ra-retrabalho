import random
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import dash
from db import PostgresSingleton

pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

 
df_veiculos = pd.read_sql('''
    select distinct "Description" as veiculos
    from veiculos_api va
    where "Description" not like '%-%'
    ''', pgEngine)['veiculos'].tolist()
    
def get_events( vehicle=50240):
    '''Consulta os eventos no banco de dados com base no veículo.'''
    query = '''
    select 
    tea."Description" as evento,
    va."Description" as veiculos,
    tpe.dia_evento:: timestamp as data_evento
    from trip_possui_evento tpe 
    left join tipos_eventos_api tea on tpe.event_type_id = tea."EventTypeId"
    left join veiculos_api va on tpe.asset_id = va."AssetId" 
    '''
    if vehicle:
        query += f''' WHERE va."Description" = '{vehicle}' '''
        df = pd.read_sql(query, pgEngine)
    return df

dash.register_page(__name__, path='/timeline', icon="material-symbols:timeline")

# Função para gerar uma cor hexadecimal aleatória
def generate_random_color():
    return f'#{random.randint(0, 0xFFFFFF):06x}'

# Função para gerar um gráfico de timeline
def generate_timeline(data):
    fig = go.Figure()

    # Dicionário para armazenar as cores dos eventos (para garantir cores únicas)
    event_colors = {}

    for event in data:
        event_type = event['evento']  # O tipo de evento é determinado pela chave 'evento'

        # Se o tipo de evento ainda não tem uma cor atribuída, gera uma cor aleatória
        if event_type not in event_colors:
            event_colors[event_type] = generate_random_color()

        # A cor associada ao tipo de evento
        color = event_colors[event_type]

        fig.add_trace(go.Scatter(
            x=[event['data_evento'], event['data_evento']],  # Momentos exatos dos eventos
            y=[event['evento']] * 2,  # Mesma posição para início e fim
            mode='markers+lines',  # Mostrar pontos e uma linha de conexão
            marker=dict(size=10, color=color),  # Cor dinâmica de acordo com o tipo de evento
            hoverinfo="text",
            hovertext=(  # Exibir detalhes ao passar o mouse sobre os pontos
                f"Viagem: {event['evento']}<br>"
                f"Data e Hora: {event['data_evento'].strftime('%d/%m/%Y %H:%M')}<br>"  # Formatação de data e hora
                f"Veículo: {event.get('veiculos', 'Não especificado')}"
            )
        ))

    fig.update_layout(
        height=600,  # Aumentar altura
        width=1000,  # Aumentar largura
        yaxis=dict(title="Viagens", automargin=True),  # Alterar título do eixo y
        xaxis=dict(title="Horário", type="date", tickformat="%H:%M"),
        margin=dict(l=50, r=50, t=30, b=50),
        title="Timeline de Eventos"
    )

    return fig

layout = html.Div([
    dcc.Dropdown(
        id='vehicle-dropdown',
        placeholder="Selecione um veículo",
        className="mb-3"
    ),
    dcc.DatePickerSingle(
        id='date-picker',
        placeholder="Selecione uma data",
        className="mb-3",
        display_format="DD/MM/YYYY"  # Formato desejado
    ),
    dcc.Dropdown(
    id='event-filter',
    options=[],  # As opções serão carregadas dinamicamente
    value=[],    # Nenhum evento selecionado por padrão
    multi=True,  # Permite selecionar múltiplos eventos
    placeholder="Selecione eventos",  # Texto exibido no dropdown
    className="mb-3"
),
    dcc.Graph(id='timeline-graph')
])


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
        vehicles = df_veiculos
    except Exception as e:
        vehicles = []
        print(f"Erro ao buscar veículos: {e}")

    dropdown_options = [{'label': vehicle, 'value': vehicle} for vehicle in vehicles]

    # Caso nenhum veículo ou data seja selecionado, retornar apenas os veículos no dropdown
    if not selected_vehicle or not selected_date:
        return dropdown_options, [], go.Figure()

    # Consultar eventos para o veículo selecionado
    try:
        events = get_events(selected_vehicle)
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
