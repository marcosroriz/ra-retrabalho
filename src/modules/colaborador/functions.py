import plotly.graph_objs as go
from datetime import datetime
import plotly.express as px

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

    # Seleciona apenas as colunas necessárias
    df_metrica = dados[["year_month_dt", "PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"]].copy()

    # Calcula a média de cada métrica por mês
    df_media = df_metrica.groupby("year_month_dt", as_index=False).mean()

    # Funde os dados para facilitar o gráfico
    df_combinado = df_media.melt(
        id_vars=["year_month_dt"],
        value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
        var_name="CATEGORIA",
        value_name="PERCENTUAL",
    )

    # Renomeia as categorias
    df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
        {"PERC_RETRABALHO": "Retrabalho", "PERC_CORRECAO_PRIMEIRA": "Correção de Primeira"}
    )

    # Gera o gráfico de linha para ambas as métricas
    fig = px.line(
        df_combinado,
        x="year_month_dt",
        y="PERCENTUAL",
        color="CATEGORIA",  # Uma linha para cada categoria
        labels={"year_month_dt": "Ano-Mês", "PERCENTUAL": "Média %", "CATEGORIA": "Métrica"},
        markers=True,
    )

    # Formata o eixo Y como porcentagem
    fig.update_yaxes(tickformat=".2f%", title_text="% Média")

    # Formata o eixo X para exibir ano e mês
    fig.update_xaxes(
        dtick="M1",
        tickformat="%Y-%b",
        title_text="Ano-Mês",
        title_standoff=90,
    )

    # Ajusta o layout do gráfico
    fig.update_layout(
        margin=dict(b=100),
        height=400,  # Altura do gráfico
    )

    return fig
