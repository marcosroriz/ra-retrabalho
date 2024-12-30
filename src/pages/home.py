#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de uma ou mais OS

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

from werkzeug.middleware.profiler import ProfilerMiddleware


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

# Obtem o quantitativo de OS por categoria
df_os_categorias_pg = pd.read_sql(
    """
    SELECT * FROM os_dados_view_agg_count
    """,
    pgEngine,
)


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, path="/", icon="material-symbols:home-outline")

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
                dbc.Col(DashIconify(icon="mdi:gear", width=45), width="auto"),
                dbc.Col(html.H1("Visão Geral das OSs", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        html.Hr(),
        # Filtros
        # dbc.Row(
        #     [
        #         dbc.Col(
        #             dbc.Card(
        #                 [
        #                     html.Div(
        #                         [
        #                             dbc.Label("Ordem de Serviço:"),
        #                             dcc.Dropdown(
        #                                 id="input-lista-os",
        #                                 options=[
        #                                     {
        #                                         "label": "TODAS AS OS",
        #                                         "value": "TODAS AS OS",
        #                                     }
        #                                 ]
        #                                 + [
        #                                     {
        #                                         "label": f"{linha['DESCRICAO DO SERVICO']} ({linha['QUANTIDADE']})",
        #                                         "value": linha["DESCRICAO DO SERVICO"],
        #                                     }
        #                                     for ix, linha in df_os_categorias_pg.iterrows()
        #                                 ],
        #                                 multi=True,
        #                                 value=["TODAS AS OS"],
        #                                 placeholder="Selecione uma ou mais OS",
        #                             ),
        #                         ],
        #                         className="dash-bootstrap",
        #                     ),
        #                 ],
        #                 body=True,
        #             ),
        #             md=12,
        #         ),
        #     ],
        # ),
        # dbc.Row(dmc.Space(h=20)),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Data (Intervalo)"),
                                    dmc.DatePicker(
                                        id="input-intervalo-datas",
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
                    md=12,
                )
            ]
        ),
        dbc.Row(dmc.Space(h=10)),
        # Conteúdo
        html.Hr(),
        dbc.Row(dmc.Space(h=10)),
        # dbc.Row(
        #     [
        #         html.H4("Indicadores"),
        #         dbc.Row(
        #             [
        #                 dbc.Col(
        #                     dbc.Card(
        #                         [
        #                             dbc.CardBody(
        #                                 dmc.Group(
        #                                     [
        #                                         dmc.Title(id="indicador-total-os", order=2),
        #                                         DashIconify(
        #                                             icon="material-symbols:order-approve-outline",
        #                                             width=48,
        #                                             color="black",
        #                                         ),
        #                                     ],
        #                                     justify="space-around",
        #                                     mt="md",
        #                                     mb="xs",
        #                                 ),
        #                             ),
        #                             dbc.CardFooter("Total de OS"),
        #                         ],
        #                         class_name="card-box-shadow",
        #                     ),
        #                     md=4,
        #                 ),
        #                 dbc.Col(
        #                     dbc.Card(
        #                         [
        #                             dbc.CardBody(
        #                                 dmc.Group(
        #                                     [
        #                                         dmc.Title(
        #                                             id="indicador-media-os-veiculo",
        #                                             order=2,
        #                                         ),
        #                                         DashIconify(
        #                                             icon="fluent:vehicle-bus-16-filled",
        #                                             width=48,
        #                                             color="black",
        #                                         ),
        #                                     ],
        #                                     justify="space-around",
        #                                     mt="md",
        #                                     mb="xs",
        #                                 ),
        #                             ),
        #                             dbc.CardFooter("Média de OS por Veículo"),
        #                         ],
        #                         class_name="card-box-shadow",
        #                     ),
        #                     md=4,
        #                 ),
        #                 dbc.Col(
        #                     dbc.Card(
        #                         [
        #                             dbc.CardBody(
        #                                 dmc.Group(
        #                                     [
        #                                         dmc.Title(
        #                                             id="indicador-media-os-mecanico",
        #                                             order=2,
        #                                         ),
        #                                         DashIconify(
        #                                             icon="mdi:mechanic",
        #                                             width=48,
        #                                             color="black",
        #                                         ),
        #                                     ],
        #                                     justify="space-around",
        #                                     mt="md",
        #                                     mb="xs",
        #                                 ),
        #                             ),
        #                             dbc.CardFooter("Média de OS por Mecânico"),
        #                         ],
        #                         class_name="card-box-shadow",
        #                     ),
        #                     md=4,
        #                 ),
        #             ]
        #         ),
        #     ]
        # ),
        # dbc.Row(dmc.Space(h=20)),
        # html.Hr(),
        dbc.Row(dmc.Space(h=10)),
        dbc.Row([html.H4("Evolução do tipo de OS por Mês"), dcc.Graph(id="graph-evolucao-tipo-os-por-mes")]),
    ]
)


##############################################################################
# CALLBACKS ##################################################################
##############################################################################
# @callback(
#     Output("graph-retrabalho-correcoes", "figure"),
#     running=[(Output("loading-overlay", "visible"), True, False)]
# )
@callback(
    Output("graph-evolucao-tipo-os-por-mes", "figure"),
    Input("input-intervalo-datas", "value"),
    running=[(Output("loading-overlay", "visible"), True, False)],
)
def plota_grafico_evolucao_tipo_os_por_mes(datas):
    if datas is None or not datas or None in datas:
        return go.Figure()

    query = """
    SELECT 
        TO_CHAR(DATE_TRUNC('month', TO_TIMESTAMP("DATA DA ABERTURA DA OS", 'YYYY-MM-DD"T"HH24:MI:SS')), 'YYYY-MM') AS month_year,
        "PRIORIDADE SERVICO" AS prioridade,
        COUNT(*) AS count
    FROM 
        os_dados
    GROUP BY 
        TO_CHAR(DATE_TRUNC('month', TO_TIMESTAMP("DATA DA ABERTURA DA OS", 'YYYY-MM-DD"T"HH24:MI:SS')), 'YYYY-MM'),
        "PRIORIDADE SERVICO" 
    ORDER BY 
        month_year, 
        prioridade;
    """
    df = pd.read_sql(query, pgEngine)

    # Arruma dt
    df["month_year_dt"] = pd.to_datetime(df["month_year"], format="%Y-%m", errors="coerce")

    # Set campo não definido
    df["prioridade"] = df["prioridade"].replace("", "Não definido")

    # Cores
    color_map = {"Não definido": "#1F77B4", "Amarelo": "#EECA3B", "Vermelho": "#D62728", "Verde": "#2CA02C"}

    # Gera o gráfico
    fig = px.line(
        df,
        x="month_year_dt",
        y="count",
        color="prioridade",
        labels={"month_year_dt": "Mês-Ano", "count": "# OS", "prioridade": "Prioridade"},
        markers=True,
        color_discrete_map=color_map,
    )

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%b %Y", title_text="Mês-Ano")

    return fig
