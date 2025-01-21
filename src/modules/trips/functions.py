import random
import plotly.graph_objects as go



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
            ), showlegend=False
        ))

    fig.update_layout(
        height=800,  # Aumentar altura
        width=1800,  # Aumentar largura
        yaxis=dict(automargin=True),  # Alterar título do eixo y
        xaxis=dict(title="Horário", type="date", tickformat="%H:%M"),
        margin=dict(l=50, r=50, t=30, b=50),
    )

    return fig