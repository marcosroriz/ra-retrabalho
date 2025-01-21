#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de um colaborador

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import math
import numpy as np
import pandas as pd
import os
import re

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import Dash, html, dcc, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Importar nossas constantes e funções utilitárias
import tema
import arq_utils
import locale_utils

# Banco de Dados
from db import PostgresSingleton

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

from modules.colaborador.colaborador_service import ColaboradorService
from modules.colaborador.functions import *

colab = ColaboradorService()


##############################################################################
# Obtêm os dados dos colaboradores
##############################################################################
# Obtem os dados dos mecânicos informados pela RA
df_mecanicos = colab.get_info_colaboradores()

# Obtêm os dados de todos os mecânicos que trabalharam na RA, mesmo os desligados
df_mecanicos_todos = colab.get_mecanicos()
##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(
    __name__, name="Retrabalho por Colaborador", path="/retrabalho-por-colaborador", icon="fluent-mdl2:timeline"
)

##############################################################################
layout = dbc.Container(
    [
        # Loading
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay",
            loaderProps={"size": "xl"},
            overlayProps={
                "radius": "lg",
                "blur": 2,
                "style": {
                    "top": 0,  # Start from the top of the viewport
                    "left": 0,  # Start from the left of the viewport
                    "width": "100vw",  # Cover the entire width of the viewport
                    "height": "100vh",  # Cover the entire height of the viewport
                },
            },
            zIndex=10,
        ),
        # Cabeçalho
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="basil:user-clock-outline", width=45), width="auto"),
                dbc.Col(html.H1("Retrabalho por Colaborador", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        html.Hr(),
        # Filtros
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Colaborador (Código):"),
                                    dcc.Dropdown(
                                        id="input-lista-colaborador",
                                        options=[
                                            {
                                                "label": f"{linha['LABEL_COLABORADOR']}",
                                                "value": linha["cod_colaborador"],
                                            }
                                            for ix, linha in df_mecanicos_todos.iterrows()
                                        ],
                                        placeholder="Selecione um colaborador",
                                    ),
                                ],
                                className="dash-bootstrap",
                            ),
                        ],
                        body=True,
                    ),
                    md=12,
                ),
            ],
        ),
        dbc.Row(dmc.Space(h=20)),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Data (Intervalo)"),
                                    dmc.DatePicker(
                                        id="input-intervalo-datas-colaborador",
                                        allowSingleDateInRange=True,
                                        type="range",
                                        minDate=date(2024, 1, 1),
                                        maxDate=date.today(),
                                        value=[date(2024, 1, 1), date.today()],
                                    ),
                                ],
                                className="dash-bootstrap",
                            ),
                        ],
                        body=True,
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Min. dias para Retrabalho"),
                                    dmc.NumberInput(id="input-min-dias-colaborador", value=30, min=1, step=1),
                                ],
                                className="dash-bootstrap",
                            ),
                        ],
                        body=True,
                    ),
                    md=6,
                ),
            ]
        ),
        # Estado
        dcc.Store(id="store-dados-colaborador-retrabalho"),
        # Inicio dos gráficos
        dbc.Row(dmc.Space(h=20)),
        # Graficos gerais
        html.Hr(),
        # Indicadores
        dbc.Row(
            [
                html.H4("Indicadores", style={"text-align": "center", "margin-bottom": "20px", 'font-size': '45px'}),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-quantidade-servico", order=2),
                                        DashIconify(
                                            icon="mdi:bomb",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",  # Centralize conteúdo no card
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total de serviços realizados"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},  # Adicione espaçamento inferior
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-total-os-trabalho", order=2),
                                        DashIconify(
                                            icon="material-symbols:order-play-outline",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total de OSs executadas"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
            ],
            justify="center",  # Centralize a linha inteira
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-correcao-de-primeira", order=2),
                                        DashIconify(
                                            icon="game-icons:time-bomb",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("OSs com correção de primeira"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-retrabalho", order=2),
                                        DashIconify(
                                            icon="tabler:reorder",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("% das OS são retrabalho"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
            ],
            justify="center",
        ),
    ],
    style={"margin-top": "20px", "margin-bottom": "20px"},
    ),
        dbc.Row(dmc.Space(h=20)),
        dbc.Row(
            [
                # Gráfico de Pizza
                dbc.Col(dbc.Row([html.H4("Atuação Geral"), dcc.Graph(id="graph-barra-atuacao-geral")]), md=4),
                # Indicadores
                dbc.Col(dbc.Row([html.H4("Atuação OS (TOP 10)"), dcc.Graph(id="graph-principais-os")]), md=8),
            ]
        ),
    ]
)

    


##############################################################################
# CALLBACKS ##################################################################
##############################################################################



@callback(
    Output("indicador-total-os-trabalho", "children"),
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
    ],
    running=[(Output("loading-overlay", "visible"), True, False)],
)
def total_os_trabalhada(id_colaborador, datas):
    dados_vazios = {"df_os_mecanico": pd.DataFrame().to_dict("records"), "vazio": True}
   
    if not id_colaborador or not datas or len(datas) != 2 or None:
        return ''

    df_os_mecanico = colab.obtem_dados_os_mecanico(id_colaborador)

    if df_os_mecanico.empty:
        return "Nenhuma OS encontrada para esse colaborador."

    
    inicio = pd.to_datetime(datas[0])
    fim = pd.to_datetime(datas[1])

    df_os_mecanico = df_os_mecanico[
        (df_os_mecanico["DATA INICIO SERVICO"] >= inicio) & (df_os_mecanico["DATA INICIO SERVICO"] <= fim)
    ]

    if df_os_mecanico.shape[0] == 0:
        return 'Nenhuma Os realizada'
    return f"{df_os_mecanico.shape[0]} OSs trabalhadas"


@callback(
    Output("indicador-quantidade-servico", "children"),
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
    ],
)
def quantidade_os_servico(id_colaborador, datas):
    dados_vazios = {"df_os_mecanico": pd.DataFrame().to_dict("records"), "vazio": True}
    # Validação dos inputs
    if not id_colaborador or not datas or len(datas) != 2 or None:
        return ''

    df_os_mecanico = colab.obtem_dados_os_mecanico(id_colaborador)

    if df_os_mecanico.empty:
        return "Nenhuma OS encontrada para esse colaborador."

    inicio = pd.to_datetime(datas[0])
    fim = pd.to_datetime(datas[1])

    df_os_mecanico = df_os_mecanico[
        (df_os_mecanico["DATA INICIO SERVICO"] >= inicio) & (df_os_mecanico["DATA INICIO SERVICO"] <= fim)
    ]
    servicos_diferentes = len(df_os_mecanico['DESCRICAO DO SERVICO'].value_counts().index)
    
    return f"{str(servicos_diferentes)} Serviços Realizados"

#####
@callback(
    Output("indicador-correcao-de-primeira", "children"),
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
    ],
)
def quantidade_correcao_primeira(id_colaborador, datas, min_dias):
    dados_vazios = {"df_os_mecanico": pd.DataFrame().to_dict("records"), "vazio": True}
    # Validação dos inputs
    if (id_colaborador is None) or (datas is None or not datas or None in datas) or (min_dias is None or min_dias < 1):
        return ''
    
    inicio = pd.to_datetime(datas[0])
    fim = pd.to_datetime(datas[1])

    df_os_mecanico = colab.obtem_dados_os_mecanico(id_colaborador)
    
    df_os_analise = colab.obtem_dados_os_sql(id_colaborador, df_os_mecanico['DESCRICAO DO SERVICO'].tolist(), inicio, fim, min_dias)
    
    df_relatorio = colab.obtem_estatistica_retrabalho_sql(df_os_analise, min_dias)
    
    correcao = df_relatorio['PERC_CORRECOES_DE_PRIMEIRA'].astype(int).sum()

    
    return f"{str(correcao)}% correções de primeira"


###
####
@callback(
    Output("indicador-retrabalho", "children"),
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
    ],
)
def quantidade_retrabalho(id_colaborador, datas, min_dias):
    dados_vazios = {"df_os_mecanico": pd.DataFrame().to_dict("records"), "vazio": True}
    # Validação dos inputs
    if (id_colaborador is None) or (datas is None or not datas or None in datas) or (min_dias is None or min_dias < 1):
        return ''
    
    inicio = pd.to_datetime(datas[0])
    fim = pd.to_datetime(datas[1])

    df_os_mecanico = colab.obtem_dados_os_mecanico(id_colaborador)
    
    df_os_analise =colab.obtem_dados_os_sql(id_colaborador, df_os_mecanico['DESCRICAO DO SERVICO'].tolist(), inicio, fim, min_dias)
    
    df_relatorio = colab.obtem_estatistica_retrabalho_sql(df_os_analise, min_dias)
    
    correcao = df_relatorio['PERC_RETRABALHO'].astype(int).sum()

    
    return f"{str(correcao)}% de retrabalho"


@callback(
    Output("store-dados-colaborador-retrabalho", "data"),
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
    ],
)
def computa_retrabalho_mecanico(id_colaborador, datas, min_dias):
    dados_vazios = {"df_os_mecanico": pd.DataFrame().to_dict("records"), "vazio": True}

    if (id_colaborador is None) or (datas is None or not datas or None in datas) or (min_dias is None or min_dias < 1):
        return dados_vazios

    # Obtem os dados de retrabalho
    df_os_mecanico = colab.obtem_dados_os_mecanico(id_colaborador)

    # Filtrar as datas
    inicio = pd.to_datetime(datas[0])
    fim = pd.to_datetime(datas[1])

    return {"df_os_mecanico": df_os_mecanico.to_dict("records"), "vazio": False}


@callback(Output("graph-barra-atuacao-geral", "figure"), Input("store-dados-colaborador-retrabalho", "data"))
def computa_atuacao_mecanico_tipo_os(data):
    if data["vazio"]:
        return go.Figure()

    # Obtem OS
    df_os_mecanico = pd.DataFrame(data["df_os_mecanico"])

    # Prepara os dados para o gráfico
    df_agg_atuacao = (
        df_os_mecanico.groupby(["DESCRICAO DO TIPO DA OS"])
        .size()
        .reset_index(name="QUANTIDADE")
        .sort_values(by="QUANTIDADE", ascending=True)
    )

    # Percentagem
    df_agg_atuacao["PERCENTAGE"] = (df_agg_atuacao["QUANTIDADE"] / df_agg_atuacao["QUANTIDADE"].sum()) * 100

    # Gera o Gráfico
    fig = px.pie(
        df_agg_atuacao,
        values="QUANTIDADE",
        names="DESCRICAO DO TIPO DA OS",
        hole=0.2,
    )

    # Update the chart to show percentages as labels
    fig.update_traces(
        textinfo="label+percent",
        texttemplate="%{value}<br>%{percent:.2%}",
    )

    fig.update_layout(
        legend=dict(
            orientation="h",  # Horizontal orientation
            y=0,  # Position the legend below the chart
            x=0.5,  # Center align the legend
            xanchor="center",
        ),
    )

    return fig


@callback(Output("graph-principais-os", "figure"), Input("store-dados-colaborador-retrabalho", "data"))
def computa_atuacao_mecanico_tipo_os(data):
    if data["vazio"]:
        return go.Figure()

    # Obtem OS
    df_os_mecanico = pd.DataFrame(data["df_os_mecanico"])

    # Prepara os dados para o gráfico
    df_agg_servico = (
        df_os_mecanico.groupby(["DESCRICAO DO SERVICO"])
        .size()
        .reset_index(name="QUANTIDADE")
        .sort_values(by="QUANTIDADE", ascending=False)
    )

    # Percentagem
    df_agg_servico["PERCENTAGE"] = (df_agg_servico["QUANTIDADE"] / df_agg_servico["QUANTIDADE"].sum()) * 100

    # Top 10 serviços
    df_agg_servico_top10 = df_agg_servico.head(10)

    # Gera o Gráfico
    fig = px.bar(
        df_agg_servico_top10,
        x="DESCRICAO DO SERVICO",
        y="QUANTIDADE",
        # orientation="h",
        text="QUANTIDADE",  # Initial text for display
    )

    fig.update_traces(
        texttemplate="%{y} (%{customdata:.1f}%)",
        customdata=df_agg_servico_top10["PERCENTAGE"],  # Add percentage data
        textposition="inside",
    )

    return fig

@callback(
    Output("graph-retrabalho-ano", "figure"), 
    [
        Input("ano-retrabalho", "value"), 
        Input("input-lista-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
    ]
)
def grafico_retrabalho_mes(id_colaborador, min_dias, ano):
    '''plota grafico de evolução de retrabalho por ano'''
    dados_vazios = {"df_os_mecanico": pd.DataFrame().to_dict("records"), "vazio": True}
    # Validação dos inputs
    if (id_colaborador is None) or (ano is None or not ano or None in ano) or (min_dias is None or min_dias < 1):
        return ''
    


    df_os_mecanico = colab.obtem_dados_os_mecanico(id_colaborador)
    
    df_os_analise = colab.obtem_dados_os_sql(id_colaborador, df_os_mecanico['DESCRICAO DO SERVICO'].tolist(), inicio, fim, min_dias)
    
    df_relatorio = colab.obtem_estatistica_retrabalho_sql(df_os_analise, min_dias)
    
    