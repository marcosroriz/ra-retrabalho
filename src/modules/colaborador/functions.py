import plotly.graph_objs as go
from datetime import datetime
import plotly.express as px
import tema


def generate_timeline_retrabalho(mouth: list, percent_retrabalho: list):
    '''Gera um grafico de linh contendo a evolução do retrabalho do colaborador '''
    fig = go.Figure(data=[go.Scatter(x=mouth, y=percent_retrabalho)])    
    return fig

def transform_year(year: str):
    '''Retorna a data do começo ao final do ano escolhido '''
    # Converte o ano para um inteiro
    year_int = int(year)
    
    # Define a data de início do ano
    start_date = datetime(year_int, 1, 1)
    
    # Define a data de término do ano
    end_date = datetime(year_int, 12, 31, 23, 59, 59)

    return start_date, end_date

def generate_grafico_evolucao(dados):
    '''Plota gráfico de evolução das médias de retrabalho e correção de primeira por mês'''

    # Funde (melt) colunas de retrabalho e correção
    df_combinado = dados.melt(
        id_vars=["year_month_dt", "escopo"],
        value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
        var_name="CATEGORIA",
        value_name="PERC",
    )

    # Renomeia as colunas
    df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
        {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
    )

    # Gera o gráfico
    fig = px.line(
        df_combinado,
        x="year_month_dt",
        y="PERC",
        color="escopo",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"escopo": "Oficina", "year_month_dt": "Ano-Mês", "PERC": "%"},
        markers=True,
    )

    # Coloca % no eixo y
    fig.update_yaxes(tickformat=".0f%")

    # Renomeia o eixo y
    fig.update_layout(
        yaxis=dict(
            title="% Retrabalho",
        ),
        yaxis2=dict(
            title="% Correção de Primeira",
            overlaying="y",
            side="right",
            anchor="x",
        ),
        margin=dict(b=100),
    )

    # Titulo
    fig.update_layout(
        annotations=[
            dict(
                text="Retrabalho por oficina (% das OS)",
                x=0.25,  # Posição X para o primeiro plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de primeira por oficina (% das OS)",
                x=0.75,  # Posição X para o segundo plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
        ]
    )

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês", title_standoff=90)

    # Aumenta o espaçamento do titulo
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))  # Increase standoff for spacing

    # Ajusta a altura do gráfico
    # fig.update_layout(
    #     height=400,  # Define a altura do gráfico
    # )

    return fig

def generate_grafico_evolucao_nota(dados):
    '''Plota gráfico de evolução das médias de retrabalho e correção de primeira por mês'''

    print(dados)
    # Gera o gráfico
    fig = px.line(
        dados,
        x="year_month",
        y="nota_media",
        color="escopo",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"escopo": "Oficina", "year_month_dt": "Ano-Mês"},
        markers=True,
    )

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês", title_standoff=90)

    # Aumenta o espaçamento do titulo
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))  # Increase standoff for spacing



    return fig

def grafico_pizza_colaborador(data):
    '''Retorna o grafico de pizza geral'''
    # Prepara os dados para o gráfico
    labels = ["Correções de Primeira", "Correções Tardias", "Retrabalhos"]
    values = [
        data["TOTAL_CORRECAO_PRIMEIRA"].values[0],
        data["TOTAL_CORRECAO_TARDIA"].values[0],
        data["TOTAL_RETRABALHO"].values[0],
    ]
    
    # Gera o gráfico
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                direction="clockwise",
                marker_colors=[tema.COR_SUCESSO, tema.COR_ALERTA, tema.COR_ERRO],
                sort=True,
            )
        ]
    )

    # Arruma legenda e texto
    fig.update_traces(textinfo="value+percent", sort=False)

    # Remove o espaçamento em torno do gráfico
    fig.update_layout(
        margin=dict(t=20, b=0),  # Remove as margens
        height=325,  # Ajuste conforme necessário
        legend=dict(
            orientation="h",  # Legenda horizontal
            yanchor="top",  # Ancora no topo
            xanchor="center",  # Centraliza
            y=-0.1,  # Coloca abaixo
            x=0.5,  # Alinha com o centro
        ),
    )

    # Retorna o gráfico
    return fig

# Função para validar o input
def input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False

    if lista_os is None or not lista_os or None in lista_os:
        return False

    return True