from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime, timedelta
import dash

dash.register_page(__name__, path='/timeline', icon="material-symbols:timeline")

# Dados de exemplo para a timeline
example_data = [
    {"vehicle": "Caminhão 1", "label": "Temperatura do Motor (Média)", "start": "2024-12-20 11:26", "end": "2024-12-20 13:41", "distance": 34},
    {"vehicle": "Caminhão 2", "label": "Rotação Excessiva", "start": "2024-12-20 12:00", "end": "2024-12-20 12:30", "distance": 10},
    {"vehicle": "Caminhão 1", "label": "Pressão do Óleo (Mínima Crítica)", "start": "2024-12-20 13:00", "end": "2024-12-20 14:00", "distance": 20},
    {"vehicle": "Caminhão 3", "label": "Velocidade Acima do Limite", "start": "2024-12-20 14:00", "end": "2024-12-20 15:00", "distance": 50},
    {"vehicle": "Caminhão 2", "label": "Consumo de Combustível Alto", "start": "2024-12-20 15:00", "end": "2024-12-20 16:00", "distance": 25},
    {"vehicle": "Caminhão 3", "label": "Freadas Bruscas", "start": "2024-12-20 16:00", "end": "2024-12-20 17:00", "distance": 15},
    {"vehicle": "Caminhão 1", "label": "Manutenção Preventiva", "start": "2024-12-20 17:00", "end": "2024-12-20 18:00", "distance": 5}
]

# Mapeamento de cores por tipo de evento
color_map = {
    "Temperatura do Motor (Média)": "#1f77b4",
    "Rotação Excessiva": "#ff7f0e",
    "Pressão do Óleo (Mínima Crítica)": "#2ca02c",
    "Velocidade Acima do Limite": "#d62728",
    "Consumo de Combustível Alto": "#9467bd",
    "Freadas Bruscas": "#8c564b",
    "Manutenção Preventiva": "#e377c2"
}

# Converter as datas dos eventos para timestamps
def convert_to_timestamp(data):
    for event in data:
        event['start_ts'] = int(datetime.strptime(event['start'], '%Y-%m-%d %H:%M').timestamp())
        event['end_ts'] = int(datetime.strptime(event['end'], '%Y-%m-%d %H:%M').timestamp())
    return data

example_data = convert_to_timestamp(example_data)

# Função para gerar um gráfico de timeline
def generate_timeline(data):
    fig = go.Figure()

    for event in data:
        fig.add_trace(go.Bar(
            x=[event['start'], event['end']],
            y=[event['label'], event['label']],
            orientation='h',
            marker=dict(color=color_map.get(event['label'], "#7f7f7f")),  # Cor dinâmica
            hoverinfo="text",
            hovertext=(
                f"Início: {event['start']}<br>Fim: {event['end']}<br>Distância: {event['distance']} km"
            )
        ))

    fig.update_layout(
        barmode='stack',
        height=400,
        yaxis=dict(title="Eventos"),
        xaxis=dict(title="Horário"),
        margin=dict(l=50, r=50, t=30, b=50)
    )

    return fig

# Layout da página
layout = html.Div([
    dcc.Dropdown(
        id='vehicle-dropdown',
        options=[
            {'label': "Caminhão 1", 'value': "Caminhão 1"},
            {'label': "Caminhão 2", 'value': "Caminhão 2"},
            {'label': "Caminhão 3", 'value': "Caminhão 3"}
        ],
        placeholder="Selecione um veículo",
        className="mb-3"
    ),
    html.Div([
        dcc.RangeSlider(
            id='date-slider',
            min=min(event['start_ts'] for event in example_data),
            max=max(event['end_ts'] for event in example_data),
            value=[
                min(event['start_ts'] for event in example_data),
                max(event['end_ts'] for event in example_data)
            ],
            marks={ts: datetime.fromtimestamp(ts).strftime('%d/%m %H:%M') for ts in 
                   range(min(event['start_ts'] for event in example_data), 
                         max(event['end_ts'] for event in example_data) + 1, 
                         3600 * 6)},  # Incrementos de 6 horas
            step=600,  # Passo de 10 minutos
            tooltip={"always_visible": True, "placement": "bottom"}
        )
    ], className="mt-4"),
    dcc.Graph(id='timeline-graph', figure=generate_timeline(example_data))
])

# Callback para atualizar a timeline
@callback(
    Output('timeline-graph', 'figure'),
    Input('vehicle-dropdown', 'value'),
    Input('date-slider', 'value')
)
def update_timeline(selected_vehicle, date_range):
    start_ts, end_ts = date_range
    filtered_data = [
        event for event in example_data
        if (not selected_vehicle or event['vehicle'] == selected_vehicle)
        and event['start_ts'] >= start_ts
        and event['end_ts'] <= end_ts
    ]
    return generate_timeline(filtered_data)
