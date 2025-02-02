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

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import Dash, html, dcc, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.subplots as sp


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

# Colaboradores / Mecânicos
df_mecanicos = pd.read_sql("SELECT * FROM colaboradores_frotas_os", pgEngine)

# Obtem a lista de OS
df_lista_os = pd.read_sql(
    """
    SELECT DISTINCT
       "DESCRICAO DA SECAO" as "SECAO",
       "DESCRICAO DO SERVICO" AS "LABEL"
    FROM 
        mat_view_retrabalho_10_dias mvrd 
    ORDER BY
        "DESCRICAO DO SERVICO"
    """,
    pgEngine,
)
lista_todas_os = df_lista_os.to_dict(orient="records")
lista_todas_os.insert(0, {"LABEL": "TODAS"})

df_lista_veiculos = pd.read_sql(
    """
    SELECT DISTINCT
    "CODIGO DO VEICULO" AS "VEICULO"
        FROM 
        mat_view_retrabalho_10_dias mvrd
    """,
    pgEngine,
)

lista_todos_veiculos = df_lista_veiculos.to_dict(orient="records")
lista_todos_veiculos.insert(0, {"VEICULO": "TODAS"})


# Tabela Top OS de Retrabalho
tbl_top_os_geral_retrabalho = [
    {"field": "DESCRICAO DO SERVICO", "headerName": "DESCRIÇÃO (PROBLEMA)", "filter": "agSetColumnFilter", "minWidth": 300},
    {"field": "TOTAL_OS", "headerName": "QTD DE OS'S", "filter": "agSetColumnFilter", "minWidth": 200},
    {"field": "PERC_RETRABALHO", "headerName": "% RETRABALHO", "filter": "agSetColumnFilter", "minWidth": 200, "valueFormatter": {"function": "params.value + '%'"},},
    # {
    #     "field": "TOTAL_OS",
    #     "headerName": "MÉDIA",
    #     "wrapHeaderText": True,
    #     "autoHeaderHeight": True,
    #     "maxWidth": 160,
    #     "filter": "agNumberColumnFilter",
    #     "type": ["numericColumn"],
    # },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORREÇÃO DE PRIMEIRA",
        "filter": "agNumberColumnFilter",
        "maxWidth": 230,
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "QUANTIDADE DE PECAS",
        "headerName": "PEÇAS TROCADAS/OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 230,
        "type": ["numericColumn"],
    },
    # {
    #     "field": "TOTAL_PROBLEMA",
    #     "headerName": "MÉDIA DE TROCA DE PEÇAS PARA ESSE MODELO",
    #     "wrapHeaderText": True,
    #     "autoHeaderHeight": True,
    #     "filter": "agNumberColumnFilter",
    #     "maxWidth": 160,
    #     "type": ["numericColumn"],
    # },
    {
        "field": "QUANTIDADE DE COLABORADORES",
        "headerName": "COLABORADORES",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 160,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
]

# Tabela Top OS Colaborador
tbl_top_colaborador_geral_retrabalho = [
    {"field": "NOME_COLABORADOR", "headerName": "Colaborador"},
    {"field": "ID_COLABORADOR", "headerName": "ID", "filter": "agNumberColumnFilter"},
    {
        "field": "TOTAL_OS",
        "headerName": "TOTAL DE OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% RETRABALHOS",
        "filter": "agNumberColumnFilter",
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORREÇÕES DE PRIMEIRA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "TOTAL_PROBLEMA",
        "headerName": "TOTAL DE PROBLEMA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "REL_OS_PROBLEMA",
        "headerName": "REL OS/PROBLEMA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
]


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Retrabalho por veículo", path="/retrabalho-por-veiculo", icon="mdi:bus-alert")

##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Loading
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay-guia-geral",
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
        dbc.Row(
            [
                dbc.Col(
                    [
                        # Cabeçalho e Inputs
                        dbc.Row(
                            [
                                html.Hr(),
                                dbc.Row(
                                    [
                                        dbc.Col(DashIconify(icon="mdi:bus-alert", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    "Retrabalho por\u00a0",
                                                    html.Strong("veículo"),
                                                ],
                                                className="align-self-center",
                                            ),
                                            width=True,
                                        ),
                                    ],
                                    align="center",
                                ),
                                dmc.Space(h=15),
                                html.Hr(),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Data (intervalo) de análise"),
                                                    dmc.DatePicker(
                                                        id="input-intervalo-datas-geral",
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
                                                    dbc.Label("Veículos"),
                                                    dcc.Dropdown(
                                                        id="input-select-veiculos",
                                                        options=[
                                                            {"label": os["VEICULO"], "value": os["VEICULO"]}
                                                            for os in lista_todos_veiculos
                                                        ],
                                                        multi=True,
                                                        value=[lista_todos_veiculos[1]["VEICULO"]] if lista_todos_veiculos else [],
                                                        placeholder="Selecione uma ou mais ordens de serviço...",
                                                    )
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
                                                    dbc.Label("Tempo (em dias) entre OS para retrabalho"),
                                                    dcc.Dropdown(
                                                        id="input-select-dias-geral-retrabalho",
                                                        options=[
                                                            {"label": "10 dias", "value": 10},
                                                            {"label": "15 dias", "value": 15},
                                                            {"label": "30 dias", "value": 30},
                                                        ],
                                                        placeholder="Período em dias",
                                                        value=10,
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Oficinas"),
                                                    dcc.Dropdown(
                                                        id="input-select-oficina-visao-geral",
                                                        options=[
                                                            {"label": "TODAS", "value": "TODAS"},
                                                            {
                                                                "label": "GARAGEM CENTRAL",
                                                                "value": "GARAGEM CENTRAL - RAL",
                                                            },
                                                            {
                                                                "label": "GARAGEM NOROESTE",
                                                                "value": "GARAGEM NOROESTE - RAL",
                                                            },
                                                            {
                                                                "label": "GARAGEM SUL",
                                                                "value": "GARAGEM SUL - RAL",
                                                            },
                                                        ],
                                                        multi=True,
                                                        value=["TODAS"],
                                                        placeholder="Selecione uma ou mais oficinas...",
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
                                                    dbc.Label("Seções (categorias) de manutenção"),
                                                    dcc.Dropdown(
                                                        id="input-select-secao-visao-geral",
                                                        options=[
                                                            {"label": "TODAS", "value": "TODAS"},
                                                            {
                                                                "label": "BORRACHARIA",
                                                                "value": "MANUTENCAO BORRACHARIA",
                                                            },
                                                            {
                                                                "label": "ELETRICA",
                                                                "value": "MANUTENCAO ELETRICA",
                                                            },
                                                            {"label": "GARAGEM", "value": "MANUTENÇÃO GARAGEM"},
                                                            {
                                                                "label": "LANTERNAGEM",
                                                                "value": "MANUTENCAO LANTERNAGEM",
                                                            },
                                                            {"label": "LUBRIFICAÇÃO", "value": "LUBRIFICAÇÃO"},
                                                            {
                                                                "label": "MECANICA",
                                                                "value": "MANUTENCAO MECANICA",
                                                            },
                                                            {"label": "PINTURA", "value": "MANUTENCAO PINTURA"},
                                                            {
                                                                "label": "SERVIÇOS DE TERCEIROS",
                                                                "value": "SERVIÇOS DE TERCEIROS",
                                                            },
                                                            {
                                                                "label": "SETOR DE ALINHAMENTO",
                                                                "value": "SETOR DE ALINHAMENTO",
                                                            },
                                                            {
                                                                "label": "SETOR DE POLIMENTO",
                                                                "value": "SETOR DE POLIMENTO",
                                                            },
                                                        ],
                                                        multi=True,
                                                        value=["TODAS"],
                                                        placeholder="Selecione uma ou mais seções...",
                                                    ),
                                                ],
                                                # className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Ordens de Serviço"),
                                                    dcc.Dropdown(
                                                        id="input-select-ordens-servico-visao-geral",
                                                        options=[
                                                            {"label": os["LABEL"], "value": os["LABEL"]}
                                                            for os in lista_todas_os
                                                        ],
                                                        multi=True,
                                                        value=["TODAS"],
                                                        placeholder="Selecione uma ou mais ordens de serviço...",
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=12,
                                ),
                            ]
                        ),
                    ],
                    md=8,
                ),
                dbc.Col(
                    # Resumo
                    dbc.Row(
                        [
                            dbc.Row(
                                [
                                    # Cabeçalho
                                    html.Hr(),
                                    dbc.Col(
                                        DashIconify(icon="wpf:statistics", width=45),
                                        width="auto",
                                    ),
                                    dbc.Col(html.H1("Resumo", className="align-self-center"), width=True),
                                    dmc.Space(h=15),
                                    html.Hr(),
                                ],
                                align="center",
                            ),
                            dmc.Space(h=30),
                            # Gráfico de pizza com a relação entre Retrabalho e Correção
                            dcc.Graph(id="graph-pizza-sintese-retrabalho-geral_veiculo"),
                        ]
                    ),
                    md=4,
                ),
            ]
        ),
                dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="material-symbols:insights", width=45), width="auto"),
                dbc.Col(
                    html.H4("Indicadores", className="align-self-center"),
                ),
                dmc.Space(h=20),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(id="indicador-porcentagem-retrabalho-veiculo", order=2),
                                                DashIconify(
                                                    icon="mdi:bus-alert",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("% retrabalho"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-porcentagem-correcao-primeira",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="ic:round-gps-fixed",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("% correção de primeira"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(id="indicador-relacao-os-problema", order=2),
                                                DashIconify(
                                                    icon="icon-park-solid:division",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Relaçao OS/problema"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                    ]
                ),
                dbc.Row(dmc.Space(h=20)),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-posicao-relaçao-retrabalho",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="ic:round-sort",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Posição veículo relaçao % retrabalho"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-posição-veiculo-correção-primeira",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="ic:round-sort",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Posição veiculo relaçao % correção de primeira"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(id="indicador-posição-veiculo-relaçao-osproblema", order=2),
                                                DashIconify(
                                                    icon="ic:round-sort",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Posição veiculo relaçao OS/Problema"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                    ]
                ),
                dbc.Row(dmc.Space(h=20)),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-pecas-totais",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:cog",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Peças total"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-pecas-mes",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:wrench",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Peças/mês"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(id="indicador-ranking-pecas", order=2),
                                                DashIconify(
                                                    icon="mdi:podium",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Ranking de peças"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                    ]
                ),
                dbc.Row(dmc.Space(h=20)),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-oss-diferentes",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="game-icons:time-bomb",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Números de OSs"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-problemas-diferentes",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:tools",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Serviços diferentes"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(id="indicador-mecanicos-diferentes", order=2),
                                                DashIconify(
                                                    icon="mdi:account-wrench",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Mecânicos diferentes"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                    ]
                ),
            ]
            
        ),
        dbc.Row(dmc.Space(h=40)),
        #dmc.Space(h=40),
        dmc.Space(h=40),
        ##Gráfico de Quantidade de OS / mes
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Relaçao de OS / mês", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-os-mes-veiculo"),
        dmc.Space(h=40),
        # Graficos de Evolução do Retrabalho por Garagem e Seção
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Relações de retrabalho / mês", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-garagem-por-mes-veiculos"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Relações de retrabalho / mês / seção", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-secao-por-mes-veiculos"),
        dmc.Space(h=40),
        #Grafico geral de peças
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Peças trocadas por mês", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-pecas-trocadas-por-mes"),
        dmc.Space(h=20),
        dag.AgGrid(
            enableEnterpriseModules=True,
            id="tabela-pecas-substituidas",
            columnDefs=[
                {"field": "OS", "autoSize": True},
                {"field": "EQUIPAMENTO", "autoSize": True},
                {"field": "MODELO", "autoSize": True},
                {"field": "PRODUTO", "autoSize": True},
                {"field": "QUANTIDADE", "autoSize": True},
                {"field": "VALOR", "autoSize": True},
                {"field": "DATA", "autoSize": True}
            ],
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Tabela por descrição de serviço", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            enableEnterpriseModules=True,
            id="tabela-descricao-de-servico",
            columnDefs=tbl_top_os_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
        ),
        dmc.Space(h=60),
        
# Indicadores

    ]
)




##############################################################################
# CALLBACKS ##################################################################
##############################################################################


# Função para validar o input
def input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False

    if lista_os is None or not lista_os or None in lista_os:
        return False
    
    if lista_veiculos is None or not lista_veiculos or None in lista_veiculos:
        return False

    return True

def input_valido2(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos, lista_modelos):
    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False

    if lista_os is None or not lista_os or None in lista_os:
        return False
    
    if lista_veiculos is None or not lista_veiculos or None in lista_veiculos:
        return False

    if lista_modelos is None or not lista_modelos or None in lista_modelos:
        return False
        
    return True
# Corrige o input para garantir que "TODAS" não seja selecionado junto com outras opções

def input_valido3(datas, min_dias, lista_veiculos):
    if datas is None or not datas or None in datas or min_dias is None:
            return False
    if lista_veiculos is None or not lista_veiculos or None in lista_veiculos:
            return False
    return True

def corrige_input(lista):
    # Caso 1: Nenhuma opcao é selecionada, reseta para "TODAS"
    if not lista:
        return ["TODAS"]

    # Caso 2: Se "TODAS" foi selecionado após outras opções, reseta para "TODAS"
    if len(lista) > 1 and "TODAS" in lista[1:]:
        return ["TODAS"]

    # Caso 3: Se alguma opção foi selecionada após "TODAS", remove "TODAS"
    if "TODAS" in lista and len(lista) > 1:
        return [value for value in lista if value != "TODAS"]

    # Por fim, se não caiu em nenhum caso, retorna o valor original
    return lista


def corrige_input_ordem_servico(lista_os, lista_secaos):
    # Vamos pegar as OS possíveis para as seções selecionadas
    df_lista_os_secao = df_lista_os

    if "TODAS" not in lista_secaos:
        df_lista_os_secao = df_lista_os_secao[df_lista_os_secao["SECAO"].isin(lista_secaos)]

    # Essa rotina garante que, ao alterar a seleção de oficinas ou seções, a lista de ordens de serviço seja coerente
    lista_os_possiveis = df_lista_os_secao.to_dict(orient="records")
    lista_os_possiveis.insert(0, {"LABEL": "TODAS"})

    lista_options = [{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_os_possiveis]

    # OK, algor vamos remover as OS que não são possíveis para as seções selecionadas
    if "TODAS" not in lista_os:
        df_lista_os_atual = df_lista_os_secao[df_lista_os_secao["LABEL"].isin(lista_os)]
        lista_os = df_lista_os_atual["LABEL"].tolist()

    return lista_options, corrige_input(lista_os)




# Subqueries para filtrar as oficinas, seções e ordens de serviço quando TODAS não for selecionado
def subquery_oficinas(lista_oficinas, prefix=""):
    query = ""
    if "TODAS" not in lista_oficinas:
        query = f"""AND {prefix}"DESCRICAO DA OFICINA" IN ({', '.join([f"'{x}'" for x in lista_oficinas])})"""

    return query


def subquery_secoes(lista_secaos, prefix=""):
    query = ""
    if "TODAS" not in lista_secaos:
        query = f"""AND {prefix}"DESCRICAO DA SECAO" IN ({', '.join([f"'{x}'" for x in lista_secaos])})"""

    return query


def subquery_os(lista_os, prefix=""):
    query = ""
    if "TODAS" not in lista_os:
        query = f"""AND {prefix}"DESCRICAO DO SERVICO" IN ({', '.join([f"'{x}'" for x in lista_os])})"""

    return query

def subquery_veiculos(lista_veiculos, prefix=""):
    query = ""
    if "TODAS" not in lista_veiculos:
        query = f"""AND {prefix}"CODIGO DO VEICULO" IN ({', '.join([f"'{x}'" for x in lista_veiculos])})"""

    return query

def subquery_equipamentos(lista_veiculos, prefix=""):
    query = ""
    if "TODAS" not in lista_veiculos:
        query = f"""AND {prefix}"EQUIPAMENTO" IN ({', '.join([f"'{x}'" for x in lista_veiculos])})"""
    return query




def subquery_modelos_veiculos(lista_modelos, prefix=""):
    query = ""
    if "TODAS" not in lista_modelos:
        query = f"""AND {prefix}"DESCRICAO DO MODELO" IN ({', '.join([f"'{x}'" for x in lista_modelos])})"""

    return query


# Callback para o grafico de síntese do retrabalho
@callback(
    [Output("graph-pizza-sintese-retrabalho-geral_veiculo", "figure"),
    Output("indicador-porcentagem-retrabalho-veiculo", "children"),
    Output("indicador-porcentagem-correcao-primeira", "children")],

    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_pizza_sintese_geral(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure(), "", ""

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)
    subquery_veiculos_os = subquery_veiculos(lista_veiculos)


    # Query
    query = f"""
        SELECT
            SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_veiculos_os}
    """

    # Executa a query
    df = pd.read_sql(query, pgEngine)

    # Calcula o total de correções tardia
    df["TOTAL_CORRECAO_TARDIA"] = df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]

    # Prepara os dados para o gráfico
    labels = ["Correções de Primeira", "Correções Tardias", "Retrabalhos"]
    values = [
        df["TOTAL_CORRECAO_PRIMEIRA"].values[0],
        df["TOTAL_CORRECAO_TARDIA"].values[0],
        df["TOTAL_RETRABALHO"].values[0],
    ]

    #print(df.head())

    total_correcao_primeira = f'''{df.iloc[0]['PERC_CORRECAO_PRIMEIRA']}%'''
    total_retrabalho = f'''{df.iloc[0]['PERC_RETRABALHO']}%'''

    #print(total_retrabalho)
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
        height=350,  # Ajuste conforme necessário
        legend=dict(
            orientation="h",  # Legenda horizontal
            yanchor="top",  # Ancora no topo
            xanchor="center",  # Centraliza
            y=-0.1,  # Coloca abaixo
            x=0.5,  # Alinha com o centro
        ),
    )

    # Retorna o gráfico
    return fig, total_correcao_primeira, total_retrabalho









########### FUNÇÃO AUXILIAR
def media_geral_retrabalho_modelos(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos, lista_modelos):
    # Chama a função input_valido com todos os parâmetros
    if not input_valido2(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos, lista_modelos):
        return go.Figure()

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)
    subquery_modelos = subquery_modelos_veiculos(lista_modelos)

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
        "CODIGO DO VEICULO",
        "DESCRICAO DO MODELO"
    FROM
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {subquery_oficinas_str} 
        {subquery_secoes_str}
        {subquery_os_str}
        {subquery_modelos}
    GROUP BY
        year_month, "CODIGO DO VEICULO", "DESCRICAO DO MODELO"
    ORDER BY
        year_month;
    """

    # Executa query
    df = pd.read_sql(query, pgEngine)

    # Arruma dt
    df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

    # Funde (melt) colunas de retrabalho e correção
    # Funde (melt) colunas de retrabalho e correção
    df_combinado = df.melt(
        id_vars=["year_month_dt", "CODIGO DO VEICULO", "DESCRICAO DO MODELO"],
        value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
        var_name="CATEGORIA",
        value_name="PERC",
    )

    #df_combinado["CODIGO DO VEICULO"] = "Geral"

    # Renomeia as colunas
    df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
        {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
    )

    df_media = df_combinado.groupby(["year_month_dt", "CATEGORIA", "DESCRICAO DO MODELO"]).agg(
        PERC=('PERC', 'mean')
    ).reset_index()

    df_media["CODIGO DO VEICULO"] = df_media["DESCRICAO DO MODELO"]

    #print(df_media.head())
    
    return df_media

def media_geral_retrabalho_geral(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Chama a função input_valido com todos os parâmetros
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure()

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
        "CODIGO DO VEICULO"
    FROM
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {subquery_oficinas_str} 
        {subquery_secoes_str}
        {subquery_os_str}
    GROUP BY
        year_month, "CODIGO DO VEICULO"
    ORDER BY
        year_month;
    """

    # Executa query
    df = pd.read_sql(query, pgEngine)

    # Arruma dt
    df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

    # Funde (melt) colunas de retrabalho e correção
    # Funde (melt) colunas de retrabalho e correção
    df_combinado = df.melt(
        id_vars=["year_month_dt", "CODIGO DO VEICULO"],
        value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
        var_name="CATEGORIA",
        value_name="PERC",
    )

    #df_combinado["CODIGO DO VEICULO"] = "Geral"

    # Renomeia as colunas
    df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
        {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
    )

    df_media = df_combinado.groupby(["year_month_dt", "CATEGORIA"]).agg(
        PERC=('PERC', 'mean')
    ).reset_index()

    df_media["CODIGO DO VEICULO"] = 'Geral'

    #print(df_media.head())
    
    return df_media


@callback(
    Output("graph-evolucao-retrabalho-por-garagem-por-mes-veiculos", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_oficina_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure()

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)
    subquery_veiculos_str = subquery_veiculos(lista_veiculos)

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
        "CODIGO DO VEICULO",
        "DESCRICAO DO MODELO"
    FROM
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {subquery_oficinas_str} 
        {subquery_secoes_str}
        {subquery_os_str}
        {subquery_veiculos_str}

    GROUP BY
        year_month, "CODIGO DO VEICULO", "DESCRICAO DO MODELO"
    ORDER BY
        year_month;
    """

    # Executa query
    df = pd.read_sql(query, pgEngine)

    # Arruma dt
    df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

    # Funde (melt) colunas de retrabalho e correção
    df_combinado = df.melt(
        id_vars=["year_month_dt", "CODIGO DO VEICULO"],
        value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
        var_name="CATEGORIA",
        value_name="PERC",
    )

    #print(media_geral.head())
    #print(media_geral)

    # Renomeia as colunas
    df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
        {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
    )

    #print(df_combinado.head())

    lista_modelos = df["DESCRICAO DO MODELO"].dropna().unique().tolist() ## preciso da lista de nomes dos modelos

    media_geral_modelos = media_geral_retrabalho_modelos(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos, lista_modelos)

    media_geral = media_geral_retrabalho_geral(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)

    #print(media_geral.head())

    df_combinado = pd.concat([df_combinado, media_geral_modelos, media_geral], ignore_index=True)

    #df_combinado = df_combinado[df_combinado["CODIGO DO VEICULO"] == "Geral"]

    #print(df_combinado.head())

    # Gera o gráfico
    fig = px.line(
        df_combinado,
        x="year_month_dt",
        y="PERC",
        color="CODIGO DO VEICULO",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"CODIGO DO VEICULO": "Veiculo", "year_month_dt": "Ano-Mês", "PERC": "%"},
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
                text="Retrabalho(%) por veículo",
                x=0.25,  # Posição X para o primeiro plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de primeira(%) por veículo",
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

    return fig


@callback(
    Output("graph-evolucao-retrabalho-por-secao-por-mes-veiculos", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure()

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)
    subquery_veiculos_str = subquery_veiculos(lista_veiculos)

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        "DESCRICAO DA SECAO",
        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
    FROM
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {subquery_oficinas_str}
        {subquery_secoes_str}
        {subquery_os_str}
        {subquery_veiculos_str}
    GROUP BY
        year_month, "DESCRICAO DA SECAO"
    ORDER BY
        year_month;
    """

    # Executa Query
    df = pd.read_sql(query, pgEngine)

    # Arruma dt
    df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

    # Funde (melt) colunas de retrabalho e correção
    df_combinado = df.melt(
        id_vars=["year_month_dt", "DESCRICAO DA SECAO"],
        value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
        var_name="CATEGORIA",
        value_name="PERC",
    )

    # Renomeia as colunas
    df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
        {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
    )

    # Multiplica por 100
    # df_combinado["PERC"] = df_combinado["PERC"] * 100

    fig = px.line(
        df_combinado,
        x="year_month_dt",
        y="PERC",
        color="DESCRICAO DA SECAO",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"DESCRICAO DA SECAO": "Seção", "year_month_dt": "Ano-Mês", "PERC": "%"},
    )

    # Ajusta o formato do eixo Y para exibir valores como porcentagem
    fig.update_yaxes(tickformat=".0f%")

    # Personaliza o layout do gráfico
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
        margin=dict(b=100),  # Espaço na parte inferior
    )

    # Adiciona títulos específicos para cada gráfico
    fig.update_layout(
        annotations=[
            dict(
                text="Retrabalho por seção (% das OS)",
                x=0.25,  # Posição X para o primeiro plot
                y=1.05,  # Posição Y acima do gráfico
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de primeira por seção (% das OS)",
                x=0.75,  # Posição X para o segundo plot
                y=1.05,  # Posição Y acima do gráfico
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
        ]
    )

    # Configura os ticks no eixo X para exibição mensal
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês", title_standoff=90)

    # Ajusta o espaçamento dos títulos do eixo X
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))


    # Exibe o gráfico
    return fig


@callback(
    [
        #Output("indicador-porcentagem-retrabalho-veiculo", "children"),
        #Output("indicador-porcentagem-correcao-primeira", "children"),
        Output("indicador-relacao-os-problema", "children"),
        Output("indicador-posicao-relaçao-retrabalho", "children"),
        Output("indicador-posição-veiculo-correção-primeira", "children"),
        Output("indicador-posição-veiculo-relaçao-osproblema", "children"),
        #Output("indicador-pecas-totais", "children"),
        #Output("indicador-pecas-mes", "children"),
        Output("indicador-ranking-pecas", "children"),
        #Output("indicador-oss-diferentes", "children"),
        #Output("indicador-problemas-diferentes", "children"),
        #Output("indicador-mecanicos-diferentes", "children"),
    ],
    Input("store-dados-os", "data"),
)
def atualiza_indicadores(data):
    # if data["vazio"]:
    #     return ["", "", "", "", "", "", "", "", "", "", "", ""]

    porcentagem_retrabalho_veiculo = '0'
    porcentagem_correcao_primeira = '0'
    rel_os_problemas = '0'
    posicao_relaçao_retrabalho = '0'


    return [
        f"{porcentagem_retrabalho_veiculo} %",
        f"{porcentagem_correcao_primeira} %",
        f"{rel_os_problemas} OS/prob",
        f"{posicao_relaçao_retrabalho}º",
        f"{posicao_veiculo_correção_primeira}º",
        f"{posicao_relaçao_relaçao-osproblema}º",
        f"{pecas_mes} peças por mês",
        f"{ranking_pecas} º",
        f"{oss_diferentes} Os's",
        f"{problemas_diferentess} diferentes",
        f"{mecanicos_diferentes} diferentes",
    ]


@callback(
    [Output('graph-evolucao-os-mes-veiculo', 'figure'),
     Output("indicador-problemas-diferentes", "children"),
     Output("indicador-mecanicos-diferentes", "children"),
     Output("indicador-oss-diferentes", "children"),],
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_evolucao_quantidade_os_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure(), "", "", ""

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)
    subquery_veiculos_str = subquery_veiculos(lista_veiculos)


    query = f"""
        SELECT 
            "CODIGO DO VEICULO",
            DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp) AS "MÊS",
            COUNT("NUMERO DA OS") AS "QUANTIDADE_DE_OS",
            "DESCRICAO DO SERVICO",
            "DESCRICAO DO MODELO",
            COUNT(DISTINCT "COLABORADOR QUE EXECUTOU O SERVICO") AS "QTD_COLABORADORES"
        FROM
            os_dados
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_veiculos_str}
        GROUP BY
            "CODIGO DO VEICULO",
            DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp),
            "DESCRICAO DO SERVICO",
            "DESCRICAO DO MODELO"
        ORDER BY
            "CODIGO DO VEICULO",
            "MÊS";
    """


    query1 = f"""
        SELECT 
            "CODIGO DO VEICULO",
            DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO") AS "MÊS",
            COUNT("NUMERO DA OS") AS "QUANTIDADE_DE_OS"
        FROM
            os_dados
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_veiculos_str}
        GROUP BY
            "CODIGO DO VEICULO",
            DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO")
        ORDER BY
            "CODIGO DO VEICULO",
            "MÊS";
    """

    query_colaboradores_diferentes = f"""
            SELECT 
            COUNT(DISTINCT "COLABORADOR QUE EXECUTOU O SERVICO") AS "TOTAL_COLABORADORES_DIFERENTES"
        FROM 
            os_dados
        WHERE 
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_veiculos_str};
    """

    query_media = f"""
        WITH os_count AS (
            SELECT 
                "CODIGO DO VEICULO",
                DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp) AS "MÊS",
                COUNT("NUMERO DA OS") AS "QUANTIDADE_DE_OS",
                COUNT(DISTINCT "DESCRICAO DO SERVICO") AS "QUANTIDADE_DE_DESCRICOES_DISTINTAS"
            FROM os_dados
            WHERE 
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
             {subquery_oficinas_str}
             {subquery_secoes_str}
             {subquery_os_str}

            GROUP BY
                "CODIGO DO VEICULO",
                DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp)
        )
        SELECT 
            "MÊS",
            SUM("QUANTIDADE_DE_OS") AS "TOTAL_DE_OS_NO_MÊS",
            AVG("QUANTIDADE_DE_OS") AS "QUANTIDADE_DE_OS",  -- MEDIA_GERAL_OS_POR_MÊS
            AVG("QUANTIDADE_DE_DESCRICOES_DISTINTAS") AS "MEDIA_DESCRICOES_DISTINTAS_POR_MÊS"
        FROM os_count
        GROUP BY
            "MÊS"
        ORDER BY
            "MÊS";
        """
    # Executa Query
    df = pd.read_sql(query, pgEngine)

    lista_modelos = df["DESCRICAO DO MODELO"].dropna().unique().tolist()
    subquery_modelos_str = subquery_modelos_veiculos(lista_modelos)

    query_media_modelos = f"""
        WITH os_count AS (
            SELECT 
                "CODIGO DO VEICULO",
                DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp) AS "MÊS",
                COUNT("NUMERO DA OS") AS "QUANTIDADE_DE_OS",
                COUNT(DISTINCT "DESCRICAO DO SERVICO") AS "QUANTIDADE_DE_DESCRICOES_DISTINTAS",
                "DESCRICAO DO MODELO"
            FROM os_dados
            WHERE 
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
             {subquery_oficinas_str}
             {subquery_secoes_str}
             {subquery_os_str}
             {subquery_modelos_str}

            GROUP BY
                "CODIGO DO VEICULO",
                DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp),
                "DESCRICAO DO MODELO"
        )
        SELECT 
            "MÊS",
            SUM("QUANTIDADE_DE_OS") AS "TOTAL_DE_OS_NO_MÊS",
            AVG("QUANTIDADE_DE_OS") AS "QUANTIDADE_DE_OS",  -- MEDIA_GERAL_OS_POR_MÊS
            AVG("QUANTIDADE_DE_DESCRICOES_DISTINTAS") AS "MEDIA_DESCRICOES_DISTINTAS_POR_MÊS",
            "DESCRICAO DO MODELO"
        FROM os_count
        GROUP BY
            "MÊS",
            "DESCRICAO DO MODELO"
        ORDER BY
            "MÊS";
        """
    df_media_modelos_str = pd.read_sql(query_media_modelos, pgEngine)

    df_media_geral = pd.read_sql(query_media, pgEngine)
    df_media_geral["CODIGO DO VEICULO"] = 'Geral'

    df_media_modelos_os = df_media_modelos_str.rename(columns={"DESCRICAO DO MODELO": "CODIGO DO VEICULO"})

    #print(df_media_modelos_str.head())

  # Novo DataFrame com a soma de OS por mês
    df_soma_mes_veiculos = df.groupby(["MÊS", "CODIGO DO VEICULO"], as_index=False)["QUANTIDADE_DE_OS"].sum()

    df_soma_mes = pd.concat([df_soma_mes_veiculos, df_media_geral, df_media_modelos_os], ignore_index=True)

    
    #print(df_soma_mes.head())
    # Gráfico 1: Quantidade de OS por Veículo e por mês
    fig1 = px.line(
        df_soma_mes,
        x="MÊS",
        y="QUANTIDADE_DE_OS",
        color="CODIGO DO VEICULO",
        labels={"MÊS": "Ano-Mês", "QUANTIDADE_DE_OS": "Quantidade de OS", "CODIGO DO VEICULO": "Código do Veículo"},
    )

    fig1.update_traces(mode="lines+markers", showlegend=True)  # Adiciona pontos às linhas e habilita legenda
    fig1.update_layout(
        title="Quantidade de Ordens de Serviço por Veículo e por mês",
        xaxis_title="Ano-Mês",
        yaxis_title="Quantidade de OS",
        margin=dict(b=100),
        showlegend=False  # Desativa a legenda no primeiro gráfico
    )

    # Processamento de dados para o segundo gráfico
    colunas_selecionadas = ['MÊS', 'MEDIA_DESCRICOES_DISTINTAS_POR_MÊS', 'CODIGO DO VEICULO']
    df_unico_geral = df_media_geral[colunas_selecionadas]
    df_unico_geral = df_unico_geral.rename(columns={'MEDIA_DESCRICOES_DISTINTAS_POR_MÊS': 'QUANTIDADE_DE_OS'})

    df_unico_modelo = df_media_modelos_os[colunas_selecionadas]
    df_unico_modelo = df_unico_modelo.rename(columns={'MEDIA_DESCRICOES_DISTINTAS_POR_MÊS': 'QUANTIDADE_DE_OS'})


    df_unico = df.drop_duplicates(subset=["DESCRICAO DO SERVICO"], keep="first")
    df_unico["DESCRICAO DO SERVICO"] = df_unico["DESCRICAO DO SERVICO"].str.strip()
    df_unico_soma = df_unico.groupby(["MÊS", "CODIGO DO VEICULO"], as_index=False)["QUANTIDADE_DE_OS"].sum()

    df_os_unicas = pd.concat([df_unico_soma, df_unico_geral, df_unico_modelo], ignore_index=True)
    df_colab_dif = pd.read_sql(query_colaboradores_diferentes, pgEngine)
    
    mecanicos_diferentes = int(df_colab_dif['TOTAL_COLABORADORES_DIFERENTES'].sum())
    os_diferentes = int(df_unico['QUANTIDADE_DE_OS'].sum())
    os_totais_veiculo = int(df_soma_mes_veiculos['QUANTIDADE_DE_OS'].sum())
    
    #print(mecanicos_diferentes)

    # Gráfico 2: Soma de OS por Mês
    fig2 = px.line(
        df_os_unicas,
        x="MÊS",
        y="QUANTIDADE_DE_OS",
        color="CODIGO DO VEICULO",
        labels={"MÊS": "Ano-Mês", "QUANTIDADE_DE_OS": "Quantidade de OS", "CODIGO DO VEICULO": "Código do Veículo"},
    )

    fig2.update_traces(mode="lines+markers", showlegend=True)  # Remove a definição explícita da cor e habilita legenda
    fig2.update_layout(
        title="Quantidade de Ordens de Serviço diferentes por Veículo e por mês",
        xaxis_title="Ano-Mês",
        yaxis_title="Quantidade de OS",
        showlegend=False  # Desativa a legenda no segundo gráfico
    )

    # Combina os gráficos em uma única visualização lado a lado
    fig = sp.make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            "Quantidade de Ordens de Serviço por Veículo e por mês",
            "Quantidade de Ordens de Serviço diferentes por Veículo e por mês",
        ],
    )

    # Adiciona os traços de cada gráfico
    for trace in fig1.data:
        fig.add_trace(trace, row=1, col=1)

    for trace in fig2.data:
        trace.showlegend = False  # Desativa a legenda para os traços do segundo gráfico
        fig.add_trace(trace, row=1, col=2)

    # Configuração geral do layout
    fig.update_layout(
        # title=dict(
        #     text="Análise de quantidade de ordens de serviço",
        #     y=0.95,  # Move o título mais para cima (valores entre 0 e 1)
        #     x=0.5,  # Centraliza o título
        #     xanchor="center",
        #     yanchor="top"
        # ),
        showlegend=True,  
        legend=dict(
            title="Código do Veículo",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1.3
        ),
        margin=dict(t=95, b=100)  # Reduz o espaço superior para puxar o título mais para cima
    )
    # Configuração dos eixos para cada subplot
    fig.update_xaxes(title_text="Ano-Mês", row=1, col=1)
    fig.update_yaxes(title_text="Quantidade de OS", row=1, col=1)
    fig.update_xaxes(title_text="Ano-Mês", row=1, col=2)
    fig.update_yaxes(title_text="Quantidade de OS", row=1, col=2)

    return fig, os_diferentes, mecanicos_diferentes, os_totais_veiculo


@callback(
    Output("graph-pecas-trocadas-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_pecas_trocadas_por_mes(datas, equipamentos):
    # Valida input
    if not datas or not equipamentos:
        return go.Figure().update_layout(title_text="Parâmetros inválidos")

    # Garante que equipamentos seja uma lista
    if isinstance(equipamentos, str):
        equipamentos = [equipamentos]
    
    # Converte equipamentos para formato compatível com SQL (lista formatada)
    equipamentos_sql = ", ".join(f"'{equip}'" for equip in equipamentos)

    # Datas
    data_inicio_str = datas[0]
    data_fim_str = datas[1]

    # Query para buscar peças trocadas por mês para os veículos selecionados
    query_veiculos = f"""
    SELECT 
        to_char("DATA"::DATE, 'YYYY-MM') AS year_month,
        "EQUIPAMENTO",
        ROUND(SUM("VALOR"), 2) AS total_pecas
    FROM 
        pecas_gerais
    WHERE 
        "EQUIPAMENTO" IN ({equipamentos_sql})
        AND "DATA"::DATE BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        AND "GRUPO" IN ('PEÇAS E EQUIPAMENTOS', 'Transmissão', 'Suspensão', 'Motores', 
                         'Sistema de Alimentacao Veiculos', 'Freios', 'Elétricos', 'Direção',
                         'Chassis', 'Carrocerias', 'Arrefecimento', 'Ar Condicionado')
    GROUP BY 
        year_month, "EQUIPAMENTO"
    ORDER BY 
        year_month;
    """

    # Query para calcular a média geral de peças trocadas por mês
    query_media_geral = f"""
    SELECT 
        to_char("DATA"::DATE, 'YYYY-MM') AS year_month,
        ROUND(SUM("VALOR") / COUNT(DISTINCT "EQUIPAMENTO"), 2) AS media_geral
    FROM 
        pecas_gerais
    WHERE 
        "DATA"::DATE BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        AND "GRUPO" IN ('PEÇAS E EQUIPAMENTOS', 'Transmissão', 'Suspensão', 'Motores', 
                         'Sistema de Alimentacao Veiculos', 'Freios', 'Elétricos', 'Direção',
                         'Chassis', 'Carrocerias', 'Arrefecimento', 'Ar Condicionado')
    GROUP BY 
        year_month
    ORDER BY 
        year_month;
    """

    try:
        # Executa a query dos veículos
        df_veiculos = pd.read_sql(query_veiculos, pgEngine)
        # Executa a query da média geral
        df_media_geral = pd.read_sql(query_media_geral, pgEngine)

        # Verifica se há dados
        if df_veiculos.empty and df_media_geral.empty:
            return go.Figure().update_layout(
                title_text="Nenhum dado disponível para o equipamento e intervalo selecionados."
            )

        # Converte a coluna de datas para datetime
        df_veiculos["year_month_dt"] = pd.to_datetime(df_veiculos["year_month"], format="%Y-%m", errors="coerce")
        df_media_geral["year_month_dt"] = pd.to_datetime(df_media_geral["year_month"], format="%Y-%m", errors="coerce")

        # Cria o gráfico de linhas
        fig = go.Figure()

        # Adiciona linhas para cada veículo selecionado
        for equip in df_veiculos["EQUIPAMENTO"].unique():
            df_equip = df_veiculos[df_veiculos["EQUIPAMENTO"] == equip]
            fig.add_trace(
                go.Scatter(
                    x=df_equip["year_month_dt"],
                    y=df_equip["total_pecas"],
                    mode="lines+markers",
                    name=f"Peças do Veículo {equip}",
                    line=dict(width=2)
                )
            )

        # Adiciona a linha para a média geral
        fig.add_trace(
            go.Scatter(
                x=df_media_geral["year_month_dt"],
                y=df_media_geral["media_geral"],
                mode="lines",
                name="Média Geral de Todos os Veículos",
                line=dict(color="orange", dash="dot", width=2),
            )
        )

        return fig
    except Exception as e:
        print(f"Erro ao executar as consultas: {e}")
        return go.Figure().update_layout(title_text=f"Erro ao carregar os dados: {e}")
    

@callback(
   [Output("tabela-pecas-substituidas", "rowData"),
    Output("indicador-pecas-totais", "children"),
    Output("indicador-pecas-mes", "children"),
    ],
    #Input("graph-pecas-trocadas-por-mes", "clickData"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def atualiza_tabela_pecas(datas, min_dias, lista_veiculos):
    # Valida input
    if not input_valido3(datas, min_dias, lista_veiculos):
        return [], 0, 0

    # Datas
    data_inicio_str = datas[0]
    
    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)

    data_inicio_dt = pd.to_datetime(data_inicio_str)
    data_inicio_str = data_inicio_dt.strftime("%d/%m/%Y")
    data_fim_str = data_fim.strftime("%d/%m/%Y")

    print(data_inicio_str)

    subquery_veiculos_str = subquery_equipamentos(lista_veiculos)

    # Obtém a data clicada no gráfico
    #selected_month = pd.to_datetime(clickData["points"][0]["x"]).strftime('%Y-%m')

    query_detalhes = f"""
    SELECT "OS", 
        "EQUIPAMENTO", 
        "MODELO", 
        "PRODUTO", 
        "QUANTIDADE", 
        "VALOR", 
        "DATA"
    FROM pecas_gerais 
        WHERE 
            TO_DATE("DATA", 'DD/MM/YY') 
                BETWEEN TO_DATE('{data_inicio_str}', 'DD/MM/YYYY') 
                    AND TO_DATE('{data_fim_str}', 'DD/MM/YYYY')
            AND "GRUPO" IN ('PEÇAS E EQUIPAMENTOS', 'Transmissão', 'Suspensão', 'Motores', 
                     'Sistema de Alimentacao Veiculos', 'Freios', 'Elétricos', 'Direção',
                     'Chassis', 'Carrocerias', 'Arrefecimento', 'Ar Condicionado')
            {subquery_veiculos_str}
    """
    
    try:
        df_detalhes = pd.read_sql(query_detalhes, pgEngine)

        df_detalhes["DT"] = pd.to_datetime(df_detalhes["DATA"], dayfirst=True)


        num_meses = df_detalhes['DT'].dt.to_period('M').nunique()

        numero_pecas_veiculos_total = int(df_detalhes['QUANTIDADE'].sum())

        #print(query_detalhes)
        print(numero_pecas_veiculos_total)
        print(num_meses)

        
        pecas_mes = round((numero_pecas_veiculos_total/num_meses), 2)

        #print(df_detalhes.head())
        return df_detalhes.to_dict("records"), numero_pecas_veiculos_total, pecas_mes
    except Exception as e:
        print(f"Erro ao executar a consulta da tabela: {e}")
        return [], 0, 0


@callback(
    Output("tabela-descricao-de-servico", "rowData"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
    running=[(Output("loading-overlay-guia-geral", "visible"), True, False)],
)
def atualiza_tabela_top_os_geral_retrabalho(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo):
        return []

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)
    subquery_veiculos_str = subquery_veiculos(lista_veiculo)

    inner_subquery_oficinas_str = subquery_oficinas(lista_oficinas, "main.")
    inner_subquery_secoes_str = subquery_secoes(lista_secaos, "main.")
    inner_subquery_os_str = subquery_os(lista_os, "main.")
    inner_subquery_veiculos_str = subquery_veiculos(lista_veiculo, "main.")

    query = f"""
    WITH normaliza_problema AS (
        SELECT
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            "DESCRICAO DO SERVICO" as servico,
            "CODIGO DO VEICULO",
            "problem_no"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_veiculos_str}
        GROUP BY
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            "DESCRICAO DO SERVICO",
            "CODIGO DO VEICULO",
            "problem_no"
    ),
    os_problema AS (
        SELECT
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            servico,
            COUNT(*) AS num_problema
        FROM
            normaliza_problema
        GROUP BY
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            servico
    )
    SELECT
        main."DESCRICAO DA OFICINA",
        main."DESCRICAO DA SECAO",
        main."DESCRICAO DO SERVICO",
        COUNT(*) AS "TOTAL_OS",
        SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
        SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
        SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
        100 * ROUND(SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
        100 * ROUND(SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
        COALESCE(op.num_problema, 0) AS "TOTAL_PROBLEMA",
        SUM(pg."QUANTIDADE") as "QUANTIDADE DE PECAS" ,
        COUNT(main."COLABORADOR QUE EXECUTOU O SERVICO") as "QUANTIDADE DE COLABORADORES" 
    FROM
        mat_view_retrabalho_{min_dias}_dias main
    LEFT JOIN
        os_problema op
    ON
        main."DESCRICAO DA OFICINA" = op."DESCRICAO DA OFICINA"
        AND main."DESCRICAO DA SECAO" = op."DESCRICAO DA SECAO"
        AND main."DESCRICAO DO SERVICO" = op.servico
    LEFT JOIN
    	PECAS_GERAIS pg
    ON 
    	main."NUMERO DA OS" = pg."OS"
    WHERE
        main."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {inner_subquery_oficinas_str}
        {inner_subquery_secoes_str}
        {inner_subquery_os_str}
        {inner_subquery_veiculos_str}
    GROUP BY
        main."DESCRICAO DA OFICINA",
        main."DESCRICAO DA SECAO",
        main."DESCRICAO DO SERVICO",
        op.num_problema
    ORDER BY
        "PERC_RETRABALHO" DESC;
    """

    # Executa a query
    df = pd.read_sql(query, pgEngine)

    df["REL_OS_PROBLEMA"] = round(df["TOTAL_OS"] / df["TOTAL_PROBLEMA"], 2)

    return df.to_dict("records")