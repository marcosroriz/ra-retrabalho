import plotly.graph_objs as go
from datetime import datetime

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