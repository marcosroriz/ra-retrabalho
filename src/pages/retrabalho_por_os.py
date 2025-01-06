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

# Colaboradores / Mecânicos
df_mecanicos = pd.read_sql("SELECT * FROM colaboradores_frotas_os", pgEngine)

# Definir colunas das tabelas de detalhamento

# Tabela Mecânicos
tbl_top_mecanicos = [
    {"field": "LABEL_COLABORADOR", "headerName": "COLABORADOR"},
    {"field": "TOTAL_OS", "headerName": "# OS"},
    {"field": "TOTAL_RETRABALHO", "headerName": "# RETRABALHOS"},
    {"field": "PERC_RETRABALHO", "headerName": "% RETRABALHOS"},
]

# Tabela OS
tbl_top_os = [
    {"field": "DIA", "headerName:": "DIA"},
    {"field": "NUMERO DA OS", "headerName": "OS"},
    {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO"},
    {"field": "DESCRICAO DO VEICULO", "headerName": "MODELO"},
    {"field": "DIAS_ATE_OS_CORRIGIR", "headerName": "DIAS ATÉ ESSA OS"},
]

# Tabel Veículos
tbl_top_vec = [
    {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO", "maxWidth": 150},
    {"field": "TOTAL_DIAS_ATE_CORRIGIR", "headerName": "TOTAL DE DIAS GASTOS ATÉ CORRIGIR"},
]

# Detalhes das OSs
tbl_detalhes_vec_os = [
    {"field": "NUMERO DA OS", "headerName": "OS", "maxWidth": 150},
    {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "minWidth": 200},
    {"field": "CLASSIFICACAO_EMOJI", "headerName": "STATUS", "maxWidth": 150},
    {"field": "LABEL_COLABORADOR", "headerName": "COLABORADOR"},
    {"field": "DIA_INICIO", "headerName": "INÍCIO", "maxWidth": 350},
    {"field": "DIA_TERMINO", "headerName": "FECHAMENTO", "maxWidth": 200},
    {"field": "DIFF_DAYS", "headerName": "DIFF DIAS COM ANT", "maxWidth": 120},
    {"field": "DIAS_ATE_OS_CORRIGIR", "headerName": "DIAS ATÉ CORRIGIR", "maxWidth": 150},
    {"field": "NUM_OS_ATE_OS_CORRIGIR", "headerName": "NUM OS ATÉ CORRIGIR", "maxWidth": 150},
    {
        "field": "COMPLEMENTO DO SERVICO",
        "headerName": "DESCRIÇÃO",
        "minWidth": 800,
        "wrapText": True,
        "autoHeight": True,
    },
]

##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Retrabalho por OS", path="/retrabalho-por-os", icon="fluent-mdl2:timeline")

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
                dbc.Col(DashIconify(icon="fluent-mdl2:timeline", width=45), width="auto"),
                dbc.Col(html.H1("Retrabalho por OS", className="align-self-center"), width=True),
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
                                    dbc.Label("Ordem de Serviço:"),
                                    dcc.Dropdown(
                                        id="input-lista-os",
                                        options=[
                                            {
                                                "label": f"{linha['DESCRICAO DO SERVICO']} ({linha['QUANTIDADE']})",
                                                "value": linha["DESCRICAO DO SERVICO"],
                                            }
                                            for ix, linha in df_os_categorias_pg.iterrows()
                                        ],
                                        multi=True,
                                        placeholder="Selecione uma ou mais OS",
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
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Min. dias para Retrabalho"),
                                    dmc.NumberInput(id="input-dias", value=30, min=1, step=1),
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
        dcc.Store(id="store-dados-os"),
        # Inicio dos gráficos
        dbc.Row(dmc.Space(h=20)),
        # Graficos gerais
        html.Hr(),
        # Indicadores
        dbc.Row(
            [
                html.H4("Indicadores"),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(id="indicador-total-problemas", order=2),
                                                DashIconify(
                                                    icon="mdi:bomb",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Total de problemas"),
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
                                                    id="indicador-total-os",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="material-symbols:order-play-outline",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Total de OS"),
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
                                                dmc.Title(id="indicador-relacao-problema-os", order=2),
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
                                    dbc.CardFooter("Relação OS/Problema"),
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
                                                    id="indicador-porcentagem-retrabalho",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="pepicons-pop:rewind-time",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("% das OS são retrabalho"),
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
                                                dmc.Title(id="indicador-num-medio-dias-correcao", order=2),
                                                DashIconify(
                                                    icon="lucide:calendar-days",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Média de dias até correção"),
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
                                                    id="indicador-num-medio-de-os-ate-correcao",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="gg:reorder",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Média de OS até correção"),
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
        # Gráfico de Pizza com a relação entre Retrabalho e Correções
        dbc.Row([html.H4("Total de OS: Correções x Retrabalho"), dcc.Graph(id="graph-retrabalho-correcoes")]),
        # dbc.Row(dmc.Space(h=20)),
        dbc.Row([html.H4("Grafículo Cumulativo Dias para Correção"), dcc.Graph(id="graph-retrabalho-cumulativo")]),
        # dbc.Row(dmc.Space(h=20)),
        dbc.Row([html.H4("Retrabalho por Modelo (%)"), dcc.Graph(id="graph-retrabalho-por-modelo-perc")]),
        # Top Colaboradores Retrabalho
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:mechanic", width=45), width="auto"),
                dbc.Col(html.H3("Ranking de Colaboradores por Retrabalho", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-media-os-colaborador", order=2),
                                        DashIconify(
                                            icon="bxs:car-mechanic",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="space-around",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Média de OS / Colaborador"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(
                                            id="indicador-media-porcentagem-retrabalho",
                                            order=2,
                                        ),
                                        DashIconify(
                                            icon="pepicons-pop:rewind-time",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="space-around",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Média da % de retrabalho dos colaboradores"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=6,
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
                                        dmc.Title(id="indicador-media-correcoes-primeira-colaborador", order=2),
                                        DashIconify(
                                            icon="gravity-ui:target-dart",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="space-around",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Média da % de correções de primeira dos colaboradores"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(
                                            id="indicador-media-correcoes-tardias-colaborador",
                                            order=2,
                                        ),
                                        DashIconify(
                                            icon="game-icons:multiple-targets",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="space-around",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Média da % de correções tardias dos colaboradores"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=6,
                ),
            ]
        ),
        dbc.Row(dmc.Space(h=20)),
        dbc.Row(
            [
                dag.AgGrid(
                    id="tabela-top-mecanicos",
                    columnDefs=tbl_top_mecanicos,
                    rowData=[],
                    defaultColDef={
                        "filter": True,
                        "floatingFilter": True,
                        "wrapHeaderText": True,
                        "initialWidth": 200,
                        "autoHeaderHeight": True,
                    },
                    columnSize="responsiveSizeToFit",
                    dashGridOptions={
                        "pagination": True,
                        "animateRows": False,
                        "localeText": locale_utils.AG_GRID_LOCALE_BR,
                    },
                ),
            ]
        ),
        html.Hr(),
        # TOP OS e Veículos
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="icon-park-outline:ranking-list", width=45), width="auto"),
                dbc.Col(
                    html.H3("Ranking de OS e Veículos por Dias até Correção", className="align-self-center"), width=True
                ),
            ],
            align="center",
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            html.H5("Ordem de Serviço"),
                            dag.AgGrid(
                                id="tabela-top-os-problematicas",
                                columnDefs=tbl_top_os,
                                rowData=[],
                                defaultColDef={"filter": True, "floatingFilter": True},
                                columnSize="responsiveSizeToFit",
                                # columnSize="sizeToFit",
                                dashGridOptions={
                                    "localeText": locale_utils.AG_GRID_LOCALE_BR,
                                    # "pagination": True,
                                    # "animateRows": False
                                },
                            ),
                        ]
                    ),
                    md=8,
                ),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4("Veículos (Soma de Dias)"),
                            dag.AgGrid(
                                id="tabela-top-veiculos",
                                columnDefs=tbl_top_vec,
                                rowData=[],
                                defaultColDef={"filter": True, "floatingFilter": True},
                                columnSize="responsiveSizeToFit",
                                dashGridOptions={
                                    "localeText": locale_utils.AG_GRID_LOCALE_BR,
                                    # "pagination": True,
                                    # "animateRows": False
                                },
                            ),
                        ]
                    ),
                    md=4,
                ),
            ]
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="hugeicons:search-list-02", width=45), width="auto"),
                dbc.Col(html.H3("Detalhar Ordens de Serviço de um Veículo", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Veículos a Detalhar:"),
                                    dcc.Dropdown(
                                        id="input-lista-vec-detalhar",
                                        options=[],
                                        placeholder="Selecione o veículo",
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
                dag.AgGrid(
                    id="tabela-detalhes-vec-os",
                    columnDefs=tbl_detalhes_vec_os,
                    rowData=[],
                    defaultColDef={
                        "filter": True,
                        "floatingFilter": True,
                        "wrapHeaderText": True,
                        "initialWidth": 200,
                        "autoHeaderHeight": True,
                    },
                    columnSize="autoSize",
                    # columnSize="sizeToFit",
                    dashGridOptions={
                        "pagination": True,
                        "animateRows": False,
                        "localeText": locale_utils.AG_GRID_LOCALE_BR,
                    },
                ),
            ]
        ),
    ]
)


##############################################################################
# CALLBACKS ##################################################################
##############################################################################


def obtem_dados_os_sql(lista_os, data_inicio, data_fim, min_dias):
    # Query
    query = f"""
    WITH os_diff_days AS (
        SELECT 
            od."NUMERO DA OS",
            od."CODIGO DO VEICULO",
            od."DESCRICAO DO SERVICO",
            od."DESCRICAO DO MODELO",
            od."DATA INICIO SERVIÇO",
            od."DATA DE FECHAMENTO DO SERVICO",
            od."COLABORADOR QUE EXECUTOU O SERVICO",
            od."COMPLEMENTO DO SERVICO",
            EXTRACT(day FROM od."DATA INICIO SERVIÇO"::timestamp without time zone - lag(od."DATA INICIO SERVIÇO"::timestamp without time zone) OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY (od."DATA INICIO SERVIÇO"::timestamp without time zone))) AS prev_days,
            EXTRACT(day FROM lead(od."DATA INICIO SERVIÇO"::timestamp without time zone) OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY (od."DATA INICIO SERVIÇO"::timestamp without time zone)) - od."DATA INICIO SERVIÇO"::timestamp without time zone) AS next_days
        FROM 
            os_dados od
        WHERE 
            od."DATA INICIO SERVIÇO" IS NOT NULL 
            AND od."DATA INICIO SERVIÇO" >= '{data_inicio}'
            AND od."DATA DE FECHAMENTO DO SERVICO" <= '{data_fim}'
            -- AND od."DESCRICAO DO SERVICO" IN ({', '.join([f"'{x}'" for x in lista_os])})
            AND (
                "DESCRICAO DO SERVICO" = 'Motor cortando alimentação'
                OR
                "DESCRICAO DO SERVICO" = 'Motor sem força'
            )
            AND od."CODIGO DO VEICULO" ='50733'
        ), 
    os_with_flags AS (
        SELECT 
            os_diff_days."NUMERO DA OS",
            os_diff_days."CODIGO DO VEICULO",
            os_diff_days."DESCRICAO DO SERVICO",
            os_diff_days."DESCRICAO DO MODELO",
            os_diff_days."DATA INICIO SERVIÇO",
            os_diff_days."DATA DE FECHAMENTO DO SERVICO",
            os_diff_days."COLABORADOR QUE EXECUTOU O SERVICO",
            os_diff_days."COMPLEMENTO DO SERVICO",
            os_diff_days.prev_days,
            os_diff_days.next_days,
            CASE
                WHEN os_diff_days.next_days <= {min_dias}::numeric THEN true
                ELSE false
            END AS retrabalho,
            CASE
                WHEN os_diff_days.next_days > {min_dias}::numeric OR os_diff_days.next_days IS NULL THEN true
                ELSE false
            END AS correcao,
            CASE
                WHEN 
                    (os_diff_days.next_days > {min_dias}::numeric OR os_diff_days.next_days IS NULL) 
                    AND 
                    (os_diff_days.prev_days > {min_dias}::numeric OR os_diff_days.prev_days IS NULL) 
                    THEN true
                ELSE false
            END AS correcao_primeira
        FROM 
            os_diff_days
        ),
    problem_grouping AS (
        SELECT 
            SUM(
                CASE
                    WHEN os_with_flags.correcao THEN 1
                    ELSE 0
                END) OVER (PARTITION BY os_with_flags."CODIGO DO VEICULO" ORDER BY os_with_flags."DATA INICIO SERVIÇO") AS problem_no,
            os_with_flags."NUMERO DA OS",
            os_with_flags."CODIGO DO VEICULO",
            os_with_flags."DESCRICAO DO SERVICO",
            os_with_flags."DESCRICAO DO MODELO",
            os_with_flags."DATA INICIO SERVIÇO",
            os_with_flags."DATA DE FECHAMENTO DO SERVICO",
            os_with_flags."COLABORADOR QUE EXECUTOU O SERVICO",
            os_with_flags."COMPLEMENTO DO SERVICO",
            os_with_flags.prev_days,
            os_with_flags.next_days,
            os_with_flags.retrabalho,
            os_with_flags.correcao,
            os_with_flags.correcao_primeira
        FROM 
            os_with_flags
        )
    
    SELECT
        CASE
            WHEN problem_grouping.retrabalho THEN problem_grouping.problem_no + 1
            ELSE problem_grouping.problem_no
        END AS problem_no,
        problem_grouping."NUMERO DA OS",
        problem_grouping."CODIGO DO VEICULO",
        problem_grouping."DESCRICAO DO MODELO",
        problem_grouping."DESCRICAO DO SERVICO",
        problem_grouping."DATA INICIO SERVIÇO",
        problem_grouping."DATA DE FECHAMENTO DO SERVICO",
        problem_grouping."COLABORADOR QUE EXECUTOU O SERVICO",
        problem_grouping."COMPLEMENTO DO SERVICO",
        problem_grouping.prev_days,
        problem_grouping.next_days,
        problem_grouping.retrabalho,
        problem_grouping.correcao,
        problem_grouping.correcao_primeira
    FROM 
        problem_grouping
    ORDER BY 
        problem_grouping."DATA INICIO SERVIÇO";
    """

    print(query)
    df_os_query = pd.read_sql_query(query, pgEngine)

    # Tratamento de datas
    df_os_query["DATA INICIO SERVICO"] = pd.to_datetime(df_os_query["DATA INICIO SERVIÇO"])
    df_os_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(df_os_query["DATA DE FECHAMENTO DO SERVICO"])

    return df_os_query


def obtem_estatistica_retrabalho_sql(df_os, min_dias):
    # Extraí os DFs
    df_retrabalho = df_os[df_os["retrabalho"]]
    df_correcao = df_os[df_os["correcao"]]
    df_correcao_primeira = df_os[df_os["correcao_primeira"]]

    # Estatísticas por modelo
    df_modelo = (
        df_os.groupby("DESCRICAO DO MODELO")
        .agg(
            {
                "NUMERO DA OS": "count",
                "retrabalho": "sum",
                "correcao": "sum",
                "correcao_primeira": "sum",
                "problem_no": lambda x: x.nunique(),  # Conta o número de problemas distintos
            }
        )
        .reset_index()
    )
    # Renomeia algumas colunas
    df_modelo = df_modelo.rename(
        columns={
            "NUMERO DA OS": "TOTAL_DE_OS",
            "retrabalho": "RETRABALHOS",
            "correcao": "CORRECOES",
            "correcao_primeira": "CORRECOES_DE_PRIMEIRA",
            "problem_no": "NUM_PROBLEMAS",
        }
    )
    # Correções Tardias
    df_modelo["CORRECOES_TARDIA"] = df_modelo["CORRECOES"] - df_modelo["CORRECOES_DE_PRIMEIRA"]
    # Calcula as porcentagens
    df_modelo["PERC_RETRABALHO"] = 100 * (df_modelo["RETRABALHOS"] / df_modelo["TOTAL_DE_OS"])
    df_modelo["PERC_CORRECOES"] = 100 * (df_modelo["CORRECOES"] / df_modelo["TOTAL_DE_OS"])
    df_modelo["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (df_modelo["CORRECOES_DE_PRIMEIRA"] / df_modelo["TOTAL_DE_OS"])
    df_modelo["PERC_CORRECOES_TARDIA"] = 100 * (df_modelo["CORRECOES_TARDIA"] / df_modelo["TOTAL_DE_OS"])
    df_modelo["REL_PROBLEMA_OS"] = df_modelo["NUM_PROBLEMAS"] / df_modelo["TOTAL_DE_OS"]

    # Estatísticas por colaborador
    df_colaborador = (
        df_os.groupby("COLABORADOR QUE EXECUTOU O SERVICO")
        .agg(
            {
                "NUMERO DA OS": "count",
                "retrabalho": "sum",
                "correcao": "sum",
                "correcao_primeira": "sum",
                "problem_no": lambda x: x.nunique(),  # Conta o número de problemas distintos
            }
        )
        .reset_index()
    )
    # Renomeia algumas colunas
    df_colaborador = df_colaborador.rename(
        columns={
            "NUMERO DA OS": "TOTAL_DE_OS",
            "retrabalho": "RETRABALHOS",
            "correcao": "CORRECOES",
            "correcao_primeira": "CORRECOES_DE_PRIMEIRA",
            "problem_no": "NUM_PROBLEMAS",
        }
    )
    # Correções Tardias
    df_colaborador["CORRECOES_TARDIA"] = df_colaborador["CORRECOES"] - df_colaborador["CORRECOES_DE_PRIMEIRA"]
    # Calcula as porcentagens
    df_colaborador["PERC_RETRABALHO"] = 100 * (df_colaborador["RETRABALHOS"] / df_colaborador["TOTAL_DE_OS"])
    df_colaborador["PERC_CORRECOES"] = 100 * (df_colaborador["CORRECOES"] / df_colaborador["TOTAL_DE_OS"])
    df_colaborador["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (
        df_colaborador["CORRECOES_DE_PRIMEIRA"] / df_colaborador["TOTAL_DE_OS"]
    )
    df_colaborador["PERC_CORRECOES_TARDIA"] = 100 * (df_colaborador["CORRECOES_TARDIA"] / df_colaborador["TOTAL_DE_OS"])
    df_colaborador["REL_PROBLEMA_OS"] = df_colaborador["NUM_PROBLEMAS"] / df_colaborador["TOTAL_DE_OS"]

    # Adiciona label de nomes
    df_colaborador["COLABORADOR QUE EXECUTOU O SERVICO"] = df_colaborador["COLABORADOR QUE EXECUTOU O SERVICO"].astype(
        int
    )

    # Encontra o nome do colaborador
    for ix, linha in df_colaborador.iterrows():
        colaborador = linha["COLABORADOR QUE EXECUTOU O SERVICO"]
        nome_colaborador = "Não encontrado"
        if colaborador in df_mecanicos["cod_colaborador"].values:
            nome_colaborador = df_mecanicos[df_mecanicos["cod_colaborador"] == colaborador]["nome_colaborador"].values[
                0
            ]
            nome_colaborador = re.sub(r"(?<!^)([A-Z])", r" \1", nome_colaborador)

        df_colaborador.at[ix, "LABEL_COLABORADOR"] = f"{int(colaborador)} - {nome_colaborador}"

    # Dias para correção
    df_dias_para_correcao = (
        df_os.groupby(["problem_no", "CODIGO DO VEICULO", "DESCRICAO DO MODELO"])
        .agg(data_inicio=("DATA INICIO SERVIÇO", "min"), data_fim=("DATA INICIO SERVIÇO", "max"))
        .reset_index()
    )
    df_dias_para_correcao["data_inicio"] = pd.to_datetime(df_dias_para_correcao["data_inicio"])
    df_dias_para_correcao["data_fim"] = pd.to_datetime(df_dias_para_correcao["data_fim"])
    df_dias_para_correcao["dias_correcao"] = (
        df_dias_para_correcao["data_fim"] - df_dias_para_correcao["data_inicio"]
    ).dt.days

    # DF estatística
    df_estatistica = pd.DataFrame(
        {
            "TOTAL_DE_OS": len(df_os),
            "TOTAL_DE_PROBLEMAS": len(df_os[df_os["correcao"]]),
            "TOTAL_DE_RETRABALHOS": len(df_os[df_os["retrabalho"]]),
            "TOTAL_DE_CORRECOES": len(df_os[df_os["correcao"]]),
            "TOTAL_DE_CORRECOES_DE_PRIMEIRA": len(df_os[df_os["correcao_primeira"]]),
            "MEDIA_DE_DIAS_PARA_CORRECAO": df_dias_para_correcao["dias_correcao"].mean(),
            "MEDIANA_DE_DIAS_PARA_CORRECAO": df_dias_para_correcao["dias_correcao"].median(),
        },
        index=[0],
    )
    # Correções tardias
    df_estatistica["TOTAL_DE_CORRECOES_TARDIAS"] = (
        df_estatistica["TOTAL_DE_CORRECOES"] - df_estatistica["TOTAL_DE_CORRECOES_DE_PRIMEIRA"]
    )
    # Rel probl/os
    df_estatistica["RELACAO_PROBLEMA_OS"] = df_estatistica["TOTAL_DE_PROBLEMAS"] / df_estatistica["TOTAL_DE_OS"]

    # Porcentagens
    df_estatistica["PERC_RETRABALHO"] = 100 * (df_estatistica["TOTAL_DE_RETRABALHOS"] / df_estatistica["TOTAL_DE_OS"])
    df_estatistica["PERC_CORRECOES"] = 100 * (df_estatistica["TOTAL_DE_CORRECOES"] / df_estatistica["TOTAL_DE_OS"])
    df_estatistica["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (
        df_estatistica["TOTAL_DE_CORRECOES_DE_PRIMEIRA"] / df_estatistica["TOTAL_DE_OS"]
    )
    df_estatistica["PERC_CORRECOES_TARDIAS"] = 100 * (
        df_estatistica["TOTAL_DE_CORRECOES_TARDIAS"] / df_estatistica["TOTAL_DE_OS"]
    )
    
    return {
        "df_estatistica": df_estatistica.to_dict("records"),
        "df_retrabalho": df_retrabalho.to_dict("records"),
        "df_correcao": df_correcao.to_dict("records"),
        "df_correcao_primeira": df_correcao_primeira.to_dict("records"),
        "df_modelo": df_modelo.to_dict("records"),
        "df_colaborador": df_colaborador.to_dict("records"),
        "df_dias_para_correcao": df_dias_para_correcao.to_dict("records"),
    }


def obtem_dados_os(lista_os):
    # Query
    query = f"""
        SELECT * FROM os_dados od
        -- WHERE "DESCRICAO DO SERVICO" IN ({', '.join([f"'{x}'" for x in lista_os])})
        -- where "DESCRICAO DO SERVICO" = 'Motor cortando alimentação' and "CODIGO DO VEICULO" ='50177'
            where 
    (
    "DESCRICAO DO SERVICO" = 'Motor cortando alimentação'
    or
    "DESCRICAO DO SERVICO" = 'Motor sem força'
    )
    and 
    "CODIGO DO VEICULO" ='50733'

    """
    df_os_query = pd.read_sql_query(query, pgEngine)

    # Tratamento de datas
    df_os_query["DATA INICIO SERVICO"] = pd.to_datetime(df_os_query["DATA INICIO SERVIÇO"])
    df_os_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(df_os_query["DATA DE FECHAMENTO DO SERVICO"])

    # TODO: Verificar se é necessário esses campos
    df_os_query["DATA_INICIO_SERVICO_DT"] = pd.to_datetime(df_os_query["DATA INICIO SERVICO"])
    df_os_query["DATA_FECHAMENTO_SERVICO_DT"] = pd.to_datetime(df_os_query["DATA DE FECHAMENTO DO SERVICO"])

    return df_os_query


def obtem_estatistica_retrabalho(df_os, min_dias):
    # Ordena os dados
    df_os_ordenada = df_os.sort_values(by=["CODIGO DO VEICULO", "DATA_INICIO_SERVICO_DT"]).reset_index(drop=True)

    # Adicionando essa coluna para obter dias e num até corrigir
    df_os_ordenada["DIAS_ATE_OS_CORRIGIR"] = -1
    df_os_ordenada["NUM_OS_ATE_OS_CORRIGIR"] = -1

    # Grupo de Problema
    grupo_problema = 0
    df_os_ordenada["GRUPO_PROBLEMA"] = grupo_problema

    # Flag para identifica OS corrigida de primeira
    df_os_ordenada["CORRIGIDA_DE_PRIMEIRA"] = False

    # Diff de days, cálculo anterior que considerava um período de 24 horas
    # df_os_ordenada["DIFF_DAYS"] = (
    #     df_os_ordenada.groupby("CODIGO DO VEICULO")["DATA_INICIO_SERVICO_DT"].diff().dt.days.fillna(0)
    # )

    # Diff de days, cálculo que considera o tempo arredondado de um dia para o outro
    df_os_ordenada["DIFF_DAYS"] = (
        df_os_ordenada.groupby("CODIGO DO VEICULO")["DATA_INICIO_SERVICO_DT"]
        .diff()
        .apply(lambda x: np.ceil(x.total_seconds() / (60 * 60 * 24)) if pd.notnull(x) else 0)
    )

    # Df que agrupa por veículo e categoria
    grouped_df = df_os_ordenada.groupby(["CODIGO DO VEICULO"])

    # Inicializa as listas/dataframes com resultados
    previous_services = []  # Para armazenar OS que fazem parte do retrabalho
    fixes = []  # Para armazenar OS que encerram o problema

    # Loop em cada veículo
    # Também processamos os veículos de forma individual
    # Podemos ter mais de um problema selecionado, decidimos agrupar para melhorar a análise do usuário
    # Para reverter ao modo antigo, onde a análise é feita por grupo, pode-se fazer o seguinte:
    # for (codigo_veiculo, descricao_servico), group in grouped_df:
    for codigo_veiculo, group in grouped_df:
        # Ordena por dia / não precisa, pois já foi ordenado
        group_df = group.reset_index(drop=True)

        # Copia para evitar warnings
        df_veiculo_sorted = group_df

        # Inicio dos dados adicionais (tempo e dias até correção)
        row_inicio_do_problema = df_veiculo_sorted.iloc[0].copy()
        num_os_ate_corrigir = 0

        # Se só tem um dado, então não tem retrabalho
        if len(df_veiculo_sorted) == 1:
            row_inicio_do_problema["DIAS_ATE_OS_CORRIGIR"] = 0
            row_inicio_do_problema["NUM_OS_ATE_OS_CORRIGIR"] = 0
            row_inicio_do_problema["CORRIGIDA_DE_PRIMEIRA"] = True
            row_inicio_do_problema["GRUPO_PROBLEMA"] = grupo_problema

            grupo_problema += 1
            # Adiciona a df_fixes
            fixes.append(row_inicio_do_problema)
            continue

        # Faz o loop para calcular serviços consecutivos
        tam_df = len(df_veiculo_sorted)

        for i in range(1, tam_df):  # Inicia da segunda linha para ter o dado anterior
            current_row = df_veiculo_sorted.iloc[i].copy()
            prev_row = df_veiculo_sorted.iloc[i - 1].copy()

            # Calcula a diferença em dias entre row_inicio_do_problema e current_row
            dia_inicio_problema = row_inicio_do_problema["DATA_INICIO_SERVICO_DT"]
            dia_inicio_correcao = prev_row["DATA_INICIO_SERVICO_DT"]
            # diferenca_dias = (dia_inicio_correcao - dia_inicio_problema).days
            diferenca_dias = np.ceil((dia_inicio_correcao - dia_inicio_problema).total_seconds() / (60 * 60 * 24))

            # Adiciona dados de tempo e numero de OS até correção, também adiciona o grupo do problema
            prev_row["DIAS_ATE_OS_CORRIGIR"] = diferenca_dias
            prev_row["NUM_OS_ATE_OS_CORRIGIR"] = num_os_ate_corrigir
            prev_row["GRUPO_PROBLEMA"] = grupo_problema

            # Verifica se o DIFF_DAY da linha atual é menor que o intervalo
            if current_row["DIFF_DAYS"] <= min_dias:
                # Adicione a linha anteiror ao retrabalho
                previous_services.append(prev_row)

                # Incrementa o Num de OS até corrigir
                num_os_ate_corrigir = num_os_ate_corrigir + 1
            else:
                # Verifica se a OS foi corrigida de primeira
                if num_os_ate_corrigir == 0:
                    prev_row["CORRIGIDA_DE_PRIMEIRA"] = True

                # Adiciona a prev_row como correção, uma vez que > min_dias
                fixes.append(prev_row)

                # Reseta linha atual como inicio do novo problema
                row_inicio_do_problema = current_row
                num_os_ate_corrigir = 0
                grupo_problema += 1

            # Verifica se é a última linha
            if i == tam_df - 1:
                # Calcula a diferença em dias entre row_inicio_do_problema e current_row
                dia_inicio_problema = row_inicio_do_problema["DATA_INICIO_SERVICO_DT"]
                dia_inicio_correcao = current_row["DATA_INICIO_SERVICO_DT"]
                diferenca_dias = (dia_inicio_correcao - dia_inicio_problema).days

                # Adiciona dados de tempo e numero de OS até correção
                current_row["DIAS_ATE_OS_CORRIGIR"] = diferenca_dias
                current_row["NUM_OS_ATE_OS_CORRIGIR"] = num_os_ate_corrigir
                current_row["GRUPO_PROBLEMA"] = grupo_problema

                # Verifica se a OS foi corrigida de primeira
                if num_os_ate_corrigir == 0:
                    current_row["CORRIGIDA_DE_PRIMEIRA"] = True

                # Adiciona ao df_fixes
                fixes.append(current_row)

                break

    # TODO: Planificar df e remover detalhamento por descrição de serviço para facilitar manipulação de dados

    # Remove duplicados e reseta os indexes
    df_previous_services = pd.DataFrame(previous_services).drop_duplicates().reset_index(drop=True)
    df_fixes = pd.DataFrame(fixes).drop_duplicates().reset_index(drop=True)

    # Obtem estatisticas de cada DF
    df_os_agg = df_os_ordenada.groupby("DESCRICAO DO SERVICO").size().reset_index(name="TOTAL_DE_OS")

    # Lida com os casos sem dados
    df_fixes_agg = df_os_agg.copy().rename(columns={"TOTAL_DE_OS": "CORRECOES"})
    df_previous_services_agg = df_os_agg.copy().rename(columns={"TOTAL_DE_OS": "RETRABALHOS"})

    if df_previous_services.empty:
        df_previous_services_agg["RETRABALHOS"] = 0
    else:
        df_previous_services_agg = (
            df_previous_services.groupby("DESCRICAO DO SERVICO").size().reset_index(name="RETRABALHOS")
        )

    if df_fixes.empty:
        df_fixes_agg["CORRECOES"] = 0
        df_fixes_agg["CORRECOES_TARDIA"] = 0
        df_fixes_agg["CORRECOES_DE_PRIMEIRA"] = 0
    else:
        df_fixes_agg = df_fixes.groupby("DESCRICAO DO SERVICO").size().reset_index(name="CORRECOES")
        df_fixes_agg_de_primeira = (
            df_fixes.groupby("DESCRICAO DO SERVICO")["CORRIGIDA_DE_PRIMEIRA"]
            .sum()
            .reset_index(name="CORRECOES_DE_PRIMEIRA")
        )
        df_fixes_agg = df_fixes_agg.merge(df_fixes_agg_de_primeira, on="DESCRICAO DO SERVICO", how="left").fillna(0)
        df_fixes_agg["CORRECOES_TARDIA"] = df_fixes_agg["CORRECOES"] - df_fixes_agg["CORRECOES_DE_PRIMEIRA"]

    # Junta eles
    df_merge = pd.merge(df_os_agg, df_previous_services_agg, on="DESCRICAO DO SERVICO", how="left").fillna(0)
    df_merge = pd.merge(df_merge, df_fixes_agg, on="DESCRICAO DO SERVICO", how="left").fillna(0)

    # Calcula as percentagens
    df_merge["PERC_RETRABALHO"] = 100 * (df_merge["RETRABALHOS"] / df_merge["TOTAL_DE_OS"])
    df_merge["PERC_CORRECOES"] = 100 * (df_merge["CORRECOES"] / df_merge["TOTAL_DE_OS"])
    df_merge["PERC_CORRECOES_TARDIA"] = 100 * (df_merge["CORRECOES_TARDIA"] / df_merge["TOTAL_DE_OS"])
    df_merge["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (df_merge["CORRECOES_DE_PRIMEIRA"] / df_merge["TOTAL_DE_OS"])

    # Ordena por percentagem
    df_merge = df_merge.sort_values(by="PERC_RETRABALHO", ascending=True)

    return df_merge, df_previous_services, df_fixes


def obtem_estatistica_colaboradores(df_fixes, df_previous_services):
    colunas_interesse = [
        "NUMERO DA OS",
        "DESCRICAO DO SERVICO",
        "DATA_INICIO_SERVICO_DT",
        "COLABORADOR QUE EXECUTOU O SERVICO",
        "GRUPO_PROBLEMA",
        "CORRIGIDA_DE_PRIMEIRA",
    ]
    df_os = pd.concat([df_fixes[colunas_interesse], df_previous_services[colunas_interesse]])

    # Total de Problemas
    total_problemas = df_os["GRUPO_PROBLEMA"].max() + 1

    # Total de OS por mecânico
    df_agg_mecanicos_total = df_os.groupby("COLABORADOR QUE EXECUTOU O SERVICO").size().reset_index(name="TOTAL_OS")

    # Participação dos mecânicos em problemas
    df_agg_mecanicos_problemas = (
        df_os.groupby("COLABORADOR QUE EXECUTOU O SERVICO")["GRUPO_PROBLEMA"]
        .nunique()
        .reset_index(name="PROBLEMAS_QUE_PARTICIPOU")
    )
    # Faz merge com total
    df_agg_mecanicos_total = df_agg_mecanicos_total.merge(
        df_agg_mecanicos_problemas, on="COLABORADOR QUE EXECUTOU O SERVICO", how="left"
    ).fillna(0)

    # Computa RETRABALHOS
    df_agg_mecanicos_retrabalhos = (
        df_previous_services.groupby("COLABORADOR QUE EXECUTOU O SERVICO").size().reset_index(name="TOTAL_RETRABALHOS")
    )
    df_agg_mecanicos_retrabalhos["TOTAL_RETRABALHOS"] = df_agg_mecanicos_retrabalhos["TOTAL_RETRABALHOS"].astype(int)
    # Faz merge com total
    df_agg_mecanicos_total = df_agg_mecanicos_total.merge(
        df_agg_mecanicos_retrabalhos, on="COLABORADOR QUE EXECUTOU O SERVICO", how="left"
    ).fillna(0)

    # Computa Correções
    df_agg_mecanicos_correcoes = (
        df_fixes.groupby("COLABORADOR QUE EXECUTOU O SERVICO").size().reset_index(name="TOTAL_CORRECOES")
    ).fillna(0)
    # Merge
    df_agg_mecanicos_total = df_agg_mecanicos_total.merge(
        df_agg_mecanicos_correcoes, on="COLABORADOR QUE EXECUTOU O SERVICO", how="left"
    ).fillna(0)

    # Computa Correções de Primeira
    df_agg_mecanicos_correcoes_primeira = (
        df_fixes.groupby("COLABORADOR QUE EXECUTOU O SERVICO")["CORRIGIDA_DE_PRIMEIRA"]
        .sum()
        .reset_index(name="TOTAL_CORRECOES_PRIMEIRA")
    )
    # Merge
    df_agg_mecanicos_total = df_agg_mecanicos_total.merge(
        df_agg_mecanicos_correcoes_primeira, on="COLABORADOR QUE EXECUTOU O SERVICO", how="left"
    ).fillna(0)

    # Computa Correções Tardia
    df_agg_mecanicos_total["TOTAL_CORRECOES_TARDIAS"] = (
        df_agg_mecanicos_total["TOTAL_CORRECOES"] - df_agg_mecanicos_total["TOTAL_CORRECOES_PRIMEIRA"]
    )

    # Percentagens
    df_agg_mecanicos_total["PERC_PROBLEMAS"] = 100 * (
        df_agg_mecanicos_total["PROBLEMAS_QUE_PARTICIPOU"] / total_problemas
    )
    df_agg_mecanicos_total["PERC_RETRABALHOS"] = 100 * (
        df_agg_mecanicos_total["TOTAL_RETRABALHOS"] / df_agg_mecanicos_total["TOTAL_OS"]
    )
    df_agg_mecanicos_total["PERC_CORRECOES"] = 100 * (
        df_agg_mecanicos_total["TOTAL_CORRECOES"] / df_agg_mecanicos_total["TOTAL_OS"]
    )
    df_agg_mecanicos_total["PERC_CORRECOES_PRIMEIRA"] = 100 * (
        df_agg_mecanicos_total["TOTAL_CORRECOES_PRIMEIRA"] / df_agg_mecanicos_total["TOTAL_CORRECOES"]
    )
    df_agg_mecanicos_total["PERC_CORRECOES_TARDIAS"] = 100 * (
        df_agg_mecanicos_total["TOTAL_CORRECOES_TARDIAS"] / df_agg_mecanicos_total["TOTAL_CORRECOES"]
    )

    # Seta ID como inteiro
    df_agg_mecanicos_total["COLABORADOR QUE EXECUTOU O SERVICO"] = df_agg_mecanicos_total[
        "COLABORADOR QUE EXECUTOU O SERVICO"
    ].astype(int)

    # Encontra o nome do colaborador
    for ix, linha in df_agg_mecanicos_total.iterrows():
        colaborador = linha["COLABORADOR QUE EXECUTOU O SERVICO"]
        nome_colaborador = "Não encontrado"
        if colaborador in df_mecanicos["cod_colaborador"].values:
            nome_colaborador = df_mecanicos[df_mecanicos["cod_colaborador"] == colaborador]["nome_colaborador"].values[
                0
            ]
            nome_colaborador = re.sub(r"(?<!^)([A-Z])", r" \1", nome_colaborador)

        df_agg_mecanicos_total.at[ix, "LABEL_COLABORADOR"] = f"{int(colaborador)} - {nome_colaborador}"

    return df_agg_mecanicos_total


@callback(
    Output("store-dados-os", "data"),
    [
        Input("input-lista-os", "value"),
        Input("input-intervalo-datas", "value"),
        Input("input-dias", "value"),
    ],
    running=[(Output("loading-overlay", "visible"), True, False)],
)
def computa_retrabalho(lista_os, datas, min_dias):
    dados_vazios = {
        "df_os": pd.DataFrame().to_dict("records"),
        "df_estatistica": pd.DataFrame().to_dict("records"),
        "df_retrabalho": pd.DataFrame().to_dict("records"),
        "df_correcao": pd.DataFrame().to_dict("records"),
        "df_correcao_primeira": pd.DataFrame().to_dict("records"),
        "df_modelo": pd.DataFrame().to_dict("records"),
        "df_colaborador": pd.DataFrame().to_dict("records"),
        "df_dias_para_correcao": pd.DataFrame().to_dict("records"),
        "vazio": True,
    }

    # Verifica se foi preenchido
    if (lista_os is None or not lista_os) or (datas is None or not datas or None in datas):
        return dados_vazios

    # Obtem datas
    inicio_data = datas[0]
    fim_data = datas[1]

    # Realiza consulta
    df_os_sql = obtem_dados_os_sql(lista_os, inicio_data, fim_data, min_dias)

    # Verifica se há dados, caso negativo retorna vazio
    df_filtro_sql = df_os_sql[
        (df_os_sql["DATA INICIO SERVICO"] >= pd.to_datetime(inicio_data))
        & (df_os_sql["DATA DE FECHAMENTO DO SERVICO"] <= pd.to_datetime(fim_data))
    ]
    if df_filtro_sql.empty:
        return dados_vazios

    # Computa retrabalho
    dict_dfs_retrabalhos = obtem_estatistica_retrabalho_sql(df_os_sql, min_dias)

    return {
        "df_os": df_filtro_sql.to_dict("records"),
        "df_estatistica": dict_dfs_retrabalhos["df_estatistica"],
        "df_retrabalho": dict_dfs_retrabalhos["df_retrabalho"],
        "df_correcao": dict_dfs_retrabalhos["df_correcao"],
        "df_correcao_primeira": dict_dfs_retrabalhos["df_correcao_primeira"],
        "df_modelo": dict_dfs_retrabalhos["df_modelo"],
        "df_colaborador": dict_dfs_retrabalhos["df_colaborador"],
        "df_dias_para_correcao": dict_dfs_retrabalhos["df_dias_para_correcao"],
        "vazio": False,
    }

    # Obtém os dados de retrabalho
    # df_os = obtem_dados_os(lista_os)

    # # Filtrar os dados
    # inicio = pd.to_datetime(datas[0])
    # fim = pd.to_datetime(datas[1])

    # # Filtrar os dados
    # df_filtro = df_os[(df_os["DATA_INICIO_SERVICO_DT"] >= inicio) & (df_os["DATA_FECHAMENTO_SERVICO_DT"] <= fim)]

    # # Obtem os dados de retrabalho
    # df_estatistica, df_previous_services, df_fixes = obtem_estatistica_retrabalho(df_filtro, min_dias)

    # # Obtem os dados dos colaboradores
    # df_os_mecanicos = obtem_estatistica_colaboradores(df_fixes, df_previous_services)

    # return {
    #     "df_estatistica": df_estatistica.to_dict("records"),
    #     "df_previous_services": df_previous_services.to_dict("records"),
    #     "df_fixes": df_fixes.to_dict("records"),
    #     "df_os_filtradas": df_filtro.to_dict("records"),
    #     "df_os_mecanicos": df_os_mecanicos.to_dict("records"),
    #     "vazio": False,
    # }


@callback(Output("graph-retrabalho-correcoes", "figure"), Input("store-dados-os", "data"))
def plota_grafico_pizza_retrabalho(data):
    if data["vazio"]:
        return go.Figure()

    # Obtém os dados de retrabalho

    df_estatistica = pd.DataFrame(data["df_estatistica"])

    # Prepara os dados para o gráfico
    labels = ["Correções de Primeira", "Correções Tardias", "Retrabalhos"]
    values = [
        df_estatistica["TOTAL_DE_CORRECOES_DE_PRIMEIRA"].values[0],
        df_estatistica["TOTAL_DE_CORRECOES_TARDIAS"].values[0],
        df_estatistica["TOTAL_DE_RETRABALHOS"].values[0]
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

    # Retorna o gráfico
    return fig


@callback(Output("graph-retrabalho-cumulativo", "figure"), Input("store-dados-os", "data"))
def plota_grafico_cumulativo_retrabalho(data):
    if data["vazio"]:
        return go.Figure()

    # Obtém os dados de dias para correção
    df_dias_para_correcao = pd.DataFrame(data["df_dias_para_correcao"])
    
    # Ordenando os dados e criando a coluna cumulativa em termos percentuais
    df_dias_para_correcao_ordenado = df_dias_para_correcao.sort_values(by="dias_correcao").copy()
    df_dias_para_correcao_ordenado["cumulative_percentage"] = (
        df_dias_para_correcao_ordenado["dias_correcao"].expanding().count() / len(df_dias_para_correcao_ordenado) * 100
    )

    # Verifica se df não está vazio
    if df_dias_para_correcao_ordenado.empty:
        return go.Figure()

    # Criando o gráfico cumulativo com o eixo y em termos percentuais
    fig = px.line(
        df_dias_para_correcao_ordenado,
        x="dias_correcao",
        y="cumulative_percentage",
        labels={"dias_correcao": "Dias", "cumulative_percentage": "Correções Cumulativas (%)"},
    )

    # Mostrando os pontos e linhas
    fig.update_traces(
        mode="markers+lines",
    )

    # Adiciona o Topo
    df_top = df_dias_para_correcao_ordenado.groupby("dias_correcao", as_index=False).agg(
        cumulative_percentage=("cumulative_percentage", "max"), count=("dias_correcao", "count")
    )
    # Reseta o index para garantir a sequencialidade
    df_top = df_top.reset_index(drop=True)
    # Adiciona o rótulo vazio
    df_top["label"] = ""

    # Vamos decidir qual a frequência dos labels
    label_frequency = 1
    num_records = len(df_top)
    if num_records >= 30:
        label_frequency = math.ceil(num_records / 20) + 1
    elif num_records >= 10:
        label_frequency = 4
    elif num_records >= 5:
        label_frequency = 2

    # Adiciona o rótulo a cada freq de registros
    for i in range(len(df_top)):
        if i % label_frequency == 0:
            df_top.at[i, "label"] = f"{df_top.at[i, 'cumulative_percentage']:.0f}% <br>({df_top.at[i, 'count']})"

    fig.add_scatter(
        x=df_top["dias_correcao"],
        y=df_top["cumulative_percentage"] + 3,
        mode="text",
        text=df_top["label"],
        textposition="middle right",
        showlegend=False,
        marker=dict(color=tema.COR_PADRAO),
    )

    fig.update_layout(
        xaxis=dict(range=[-1, df_dias_para_correcao_ordenado["dias_correcao"].max() + 3]),
    )

    # Retorna o gráfico
    return fig


@callback(Output("graph-retrabalho-por-modelo-perc", "figure"), Input("store-dados-os", "data"))
def plota_grafico_barras_retrabalho_por_modelo_perc(data):
    if data["vazio"]:
        return go.Figure()

    #####
    # Obtém os dados de retrabalho
    #####
    df_previous_services = pd.DataFrame(data["df_previous_services"])
    df_fixes = pd.DataFrame(data["df_fixes"])
    df_os_filtradas = pd.DataFrame(data["df_os_filtradas"])

    # Agrupa por modelo, vamos criar os dataframes para cada modelo
    df_os_agg_por_modelo = df_os_filtradas.groupby(["DESCRICAO DO MODELO"]).size().reset_index(name="TOTAL_DE_OS")

    # Primeiro, cria os dataframes para cada modelo com valores numéricos zerados
    df_previous_agg_por_modelo = df_os_agg_por_modelo.copy()
    df_previous_agg_por_modelo["RETRABALHOS"] = 0

    df_fixes_agg_por_modelo = df_os_agg_por_modelo.copy()
    df_fixes_agg_por_modelo["CORRECOES"] = 0
    df_fixes_agg_por_modelo["CORRECOES_TARDIA"] = 0
    df_fixes_agg_por_modelo["CORRECOES_DE_PRIMEIRA"] = 0

    # Agora, preenche os valores numéricos
    if not df_previous_services.empty:
        df_previous_agg_por_modelo = (
            df_previous_services.groupby(["DESCRICAO DO MODELO"]).size().reset_index(name="RETRABALHOS")
        )

    if not df_fixes.empty:
        df_fixes_agg_por_modelo = df_fixes.groupby(["DESCRICAO DO MODELO"]).size().reset_index(name="CORRECOES")
        df_agg_corr_primeira = (
            df_fixes[df_fixes["CORRIGIDA_DE_PRIMEIRA"]]
            .groupby(["DESCRICAO DO MODELO"])
            .size()
            .reset_index(name="CORRECOES_DE_PRIMEIRA")
        )
        df_agg_corr_tardia = (
            df_fixes[~df_fixes["CORRIGIDA_DE_PRIMEIRA"]]
            .groupby(["DESCRICAO DO MODELO"])
            .size()
            .reset_index(name="CORRECOES_TARDIA")
        )
        df_fixes_agg_por_modelo = pd.merge(
            df_fixes_agg_por_modelo, df_agg_corr_primeira, on=["DESCRICAO DO MODELO"], how="left"
        )
        df_fixes_agg_por_modelo = pd.merge(
            df_fixes_agg_por_modelo, df_agg_corr_tardia, on=["DESCRICAO DO MODELO"], how="left"
        )
        df_fixes_agg_por_modelo = df_fixes_agg_por_modelo.fillna(0)

    # Faz o merge
    df_merge_modelo = pd.merge(
        df_os_agg_por_modelo,
        df_previous_agg_por_modelo,
        on=["DESCRICAO DO MODELO"],
        how="outer",
    )
    df_merge_modelo = pd.merge(df_merge_modelo, df_fixes_agg_por_modelo, on=["DESCRICAO DO MODELO"], how="outer")
    df_merge_modelo = df_merge_modelo.fillna(0)
    df_merge_modelo = df_merge_modelo.astype({"CORRECOES": int, "RETRABALHOS": int, "TOTAL_DE_OS": int})

    # Computa as percentagens
    df_merge_modelo["PERC_RETRABALHO"] = 100 * (df_merge_modelo["RETRABALHOS"] / df_merge_modelo["TOTAL_DE_OS"])
    df_merge_modelo["PERC_CORRECOES"] = 100 * (df_merge_modelo["CORRECOES"] / df_merge_modelo["TOTAL_DE_OS"])
    df_merge_modelo["PERC_CORRECOES_TARDIA"] = 100 * (
        df_merge_modelo["CORRECOES_TARDIA"] / df_merge_modelo["TOTAL_DE_OS"]
    )
    df_merge_modelo["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (
        df_merge_modelo["CORRECOES_DE_PRIMEIRA"] / df_merge_modelo["TOTAL_DE_OS"]
    )

    # Gera o gráfico
    bar_chart = px.bar(
        df_merge_modelo,
        x="DESCRICAO DO MODELO",
        y=["PERC_CORRECOES_DE_PRIMEIRA", "PERC_CORRECOES_TARDIA", "PERC_RETRABALHO"],
        barmode="stack",
        color_discrete_sequence=[tema.COR_SUCESSO, tema.COR_ALERTA, tema.COR_ERRO],
        labels={
            "value": "Percentagem",
            "DESCRICAO DO SERVICO": "Ordem de Serviço",
            "variable": "Itens",
        },
    )

    # Atualizando os valores de rótulo para PERC_CORRECOES_DE_PRIMEIRA (percentual e valor absoluto de correções de primeira)
    bar_chart.update_traces(
        text=[
            f"{retrabalho} ({perc_retrab:.2f}%)"
            for retrabalho, perc_retrab in zip(
                df_merge_modelo["CORRECOES_DE_PRIMEIRA"], df_merge_modelo["PERC_CORRECOES_DE_PRIMEIRA"]
            )
        ],
        selector=dict(name="PERC_CORRECOES_DE_PRIMEIRA"),
    )

    # Atualizando os valores de rótulo para PERC_CORRECOES_TARDIA (percentual e valor absoluto de correções tardias)
    bar_chart.update_traces(
        text=[
            f"{correcoes} ({perc_correcoes:.2f}%)"
            for correcoes, perc_correcoes in zip(
                df_merge_modelo["CORRECOES_TARDIA"], df_merge_modelo["PERC_CORRECOES_TARDIA"]
            )
        ],
        selector=dict(name="PERC_CORRECOES_TARDIA"),
    )

    # Atualizando os valores de rótulo para PERC_RETRABALHO (percentual e valor absoluto de retrabalhos)
    bar_chart.update_traces(
        text=[
            f"{correcoes} ({perc_correcoes:.2f}%)"
            for correcoes, perc_correcoes in zip(df_merge_modelo["RETRABALHOS"], df_merge_modelo["PERC_RETRABALHO"])
        ],
        selector=dict(name="PERC_RETRABALHO"),
    )

    # Exibir os rótulos nas barras
    bar_chart.update_traces(texttemplate="%{text}")

    # Ajustar a margem inferior para evitar corte de rótulos
    bar_chart.update_layout(margin=dict(b=200), height=600)

    # Retorna o gráfico
    return bar_chart


@callback(
    [
        Output("indicador-total-problemas", "children"),
        Output("indicador-total-os", "children"),
        Output("indicador-relacao-problema-os", "children"),
        Output("indicador-porcentagem-retrabalho", "children"),
        Output("indicador-num-medio-dias-correcao", "children"),
        Output("indicador-num-medio-de-os-ate-correcao", "children"),
    ],
    Input("store-dados-os", "data"),
)
def atualiza_indicadores(data):
    if data["vazio"]:
        return ["", "", "", "", "", ""]

    #####
    # Obtém os dados de retrabalho
    #####
    df_estatistica = pd.DataFrame(data["df_estatistica"])
    df_fixes = pd.DataFrame(data["df_fixes"])

    # Valores
    total_de_problemas = int(np.max(df_fixes["GRUPO_PROBLEMA"]) + 1)
    total_de_os = int(df_estatistica["TOTAL_DE_OS"].sum())
    rel_os_problemas = round(float(total_de_os / total_de_problemas), 2)

    perc_retrabalho = round(100 * float(df_estatistica["RETRABALHOS"].sum() / df_estatistica["TOTAL_DE_OS"].sum()), 2)
    dias_ate_corrigir = round(float(df_fixes["DIAS_ATE_OS_CORRIGIR"].mean()), 2)
    num_os_ate_corrigir = round(float(df_fixes["NUM_OS_ATE_OS_CORRIGIR"].mean()), 2)

    return [
        f"{total_de_problemas} problemas",
        f"{total_de_os} OS",
        f"{rel_os_problemas} OS/prob",
        f"{perc_retrabalho}%",
        f"{dias_ate_corrigir} dias",
        f"{num_os_ate_corrigir} OS",
    ]


@callback(
    [
        Output("indicador-media-os-colaborador", "children"),
        Output("indicador-media-porcentagem-retrabalho", "children"),
        Output("indicador-media-correcoes-primeira-colaborador", "children"),
        Output("indicador-media-correcoes-tardias-colaborador", "children"),
    ],
    Input("store-dados-os", "data"),
)
def atualiza_indicadores_mecanico(data):
    if data["vazio"]:
        return ["", "", "", ""]

    #####
    # Obtém os dados de retrabalho
    #####
    df_previous_services = pd.DataFrame(data["df_previous_services"])
    df_os_filtradas = pd.DataFrame(data["df_os_filtradas"])
    df_os_mecanicos = pd.DataFrame(data["df_os_mecanicos"])

    # Total de OS
    total_os = df_os_mecanicos["TOTAL_OS"].sum()

    # Média de OS por mecânico
    media_os_por_mecanico = round(float(df_os_mecanicos["TOTAL_OS"].mean()), 2)

    # Retrabalhos médios
    media_retrabalhos_por_mecanico = round(float(df_os_mecanicos["PERC_RETRABALHOS"].mean()), 2)

    # Correções de Primeira
    media_correcoes_primeira = round(float(df_os_mecanicos["PERC_CORRECOES_PRIMEIRA"].mean()), 2)

    # Correções Tardias
    media_correcoes_tardias = round(float(df_os_mecanicos["PERC_CORRECOES_TARDIAS"].mean()), 2)

    return [
        f"{media_os_por_mecanico} OS / colaborador",
        f"{media_retrabalhos_por_mecanico}%",
        f"{media_correcoes_primeira}%",
        f"{media_correcoes_tardias}%",
    ]


@callback(
    Output("tabela-top-mecanicos", "rowData"),
    Input("store-dados-os", "data"),
)
def update_tabela_mecanicos_retrabalho(data):
    if data["vazio"]:
        return []

    #####
    # Obtém os dados de retrabalho
    #####
    df_previous_services = pd.DataFrame(data["df_previous_services"])
    df_fixes = pd.DataFrame(data["df_fixes"])
    df_os_filtradas = pd.DataFrame(data["df_os_filtradas"])

    # Total de OS
    df_total_os_por_mecanico = (
        df_os_filtradas.groupby(["COLABORADOR QUE EXECUTOU O SERVICO"]).size().reset_index(name="TOTAL_OS")
    )

    # Retrabalhos
    # Lida com os casos sem dados
    df_total_retrabalho_por_mecanico = df_total_os_por_mecanico.copy().rename(columns={"TOTAL_OS": "TOTAL_RETRABALHO"})

    if df_previous_services.empty:
        df_total_retrabalho_por_mecanico["TOTAL_RETRABALHO"] = 0
    else:
        df_total_retrabalho_por_mecanico = (
            df_previous_services.groupby("COLABORADOR QUE EXECUTOU O SERVICO")
            .size()
            .reset_index(name="TOTAL_RETRABALHO")
        )

    # Corrigidas de primeiro
    df_total_fixes_por_mecanico = df_total_os_por_mecanico.copy()

    if df_fixes.empty:
        df_total_fixes_por_mecanico["TOTAL_CORRIGIDA_DE_PRIMEIRA"] = 0
    else:
        df_total_fixes_por_mecanico = (
            df_fixes.groupby("COLABORADOR QUE EXECUTOU O SERVICO")["CORRIGIDA_DE_PRIMEIRA"]
            .sum()
            .reset_index(name="TOTAL_CORRIGIDA_DE_PRIMEIRA")
        )

    # Merge
    df_total_mecanico = df_total_os_por_mecanico.merge(df_total_retrabalho_por_mecanico, how="left")
    df_total_mecanico = df_total_mecanico.merge(df_total_fixes_por_mecanico, how="left")

    # Seta 0 para aqueles que não estão no retrabalho ou nao tiveram correções de primeira
    df_total_mecanico = df_total_mecanico.fillna(0)

    # Calcula correções tardias e total de correções
    df_total_mecanico["TOTAL_CORRECOES_TARDIA"] = (
        df_total_mecanico["TOTAL_OS"] - df_total_mecanico["TOTAL_CORRIGIDA_DE_PRIMEIRA"]
    )
    df_total_mecanico["TOTAL_CORRECOES"] = (
        df_total_mecanico["TOTAL_CORRECOES_TARDIA"] + df_total_mecanico["TOTAL_CORRIGIDA_DE_PRIMEIRA"]
    )

    # Calcula a participação do mecânico nos problemas

    df_total_mecanico["TOTAL_RETRABALHO"] = df_total_mecanico["TOTAL_RETRABALHO"].fillna(0)

    # Calcula a percentagem
    df_total_mecanico["PERC_RETRABALHO"] = 100 * (df_total_mecanico["TOTAL_RETRABALHO"] / df_total_mecanico["TOTAL_OS"])
    # Ordena por percentagem
    df_total_mecanico = df_total_mecanico.sort_values(by="PERC_RETRABALHO", ascending=False)
    # Formata a percentagem em 2 casas decimais
    df_total_mecanico["PERC_RETRABALHO"] = df_total_mecanico["PERC_RETRABALHO"].round(2)
    # Adiciona o símbolo de porcentagem
    df_total_mecanico["PERC_RETRABALHO"] = df_total_mecanico["PERC_RETRABALHO"].astype(str) + "%"

    # Encontra o nome do colaborador
    for ix, linha in df_total_mecanico.iterrows():
        colaborador = linha["COLABORADOR QUE EXECUTOU O SERVICO"]
        nome_colaborador = "Não encontrado"
        if colaborador in df_mecanicos["cod_colaborador"].values:
            nome_colaborador = df_mecanicos[df_mecanicos["cod_colaborador"] == colaborador]["nome_colaborador"].values[
                0
            ]
            nome_colaborador = re.sub(r"(?<!^)([A-Z])", r" \1", nome_colaborador)

        df_total_mecanico.at[ix, "LABEL_COLABORADOR"] = f"{int(colaborador)} - {nome_colaborador}"

    # Retorna tabela
    return df_total_mecanico.to_dict("records")


@callback(
    Output("tabela-top-os-problematicas", "rowData"),
    Input("store-dados-os", "data"),
)
def update_tabela_os_problematicas(data):
    if data["vazio"]:
        return []

    #####
    # Obtém os dados de retrabalho
    #####
    df_fixes = pd.DataFrame(data["df_fixes"])

    df_tabela = df_fixes.sort_values(by=["DIAS_ATE_OS_CORRIGIR"], ascending=False).copy()
    df_tabela["DIA"] = pd.to_datetime(df_tabela["DATA_INICIO_SERVICO_DT"]).dt.strftime("%d/%m/%Y")

    # Retorna tabela
    return df_tabela.to_dict("records")


@callback(
    Output("tabela-top-veiculos", "rowData"),
    Input("store-dados-os", "data"),
)
def update_tabela_veiculos_problematicos(data):
    if data["vazio"]:
        return []

    #####
    # Obtém os dados de retrabalho
    #####
    df_fixes = pd.DataFrame(data["df_fixes"])

    df_top_veiculos = (
        df_fixes.groupby("CODIGO DO VEICULO")["DIAS_ATE_OS_CORRIGIR"].sum().reset_index(name="TOTAL_DIAS_ATE_CORRIGIR")
    )
    df_top_veiculos = df_top_veiculos.sort_values(by="TOTAL_DIAS_ATE_CORRIGIR", ascending=False)

    # Retorna tabela
    return df_top_veiculos.to_dict("records")


@callback(
    Output("input-lista-vec-detalhar", "options"),
    Input("store-dados-os", "data"),
)
def update_lista_veiculos_detalhar(data):
    if data["vazio"]:
        return []

    #####
    # Obtém os dados de retrabalho
    #####
    df_fixes = pd.DataFrame(data["df_fixes"])

    # Ordena veículos por dias até corrigir
    df_top_veiculos = (
        df_fixes.groupby("CODIGO DO VEICULO")["DIAS_ATE_OS_CORRIGIR"].sum().reset_index(name="TOTAL_DIAS_ATE_CORRIGIR")
    )
    df_top_veiculos = df_top_veiculos.sort_values(by="TOTAL_DIAS_ATE_CORRIGIR", ascending=False)

    # Gera a lista de opções
    vec_list = [
        {
            "label": f"{linha['CODIGO DO VEICULO']} ({linha['TOTAL_DIAS_ATE_CORRIGIR']} dias até correção)",
            "value": linha["CODIGO DO VEICULO"],
        }
        for _, linha in df_top_veiculos.iterrows()
    ]

    return vec_list


@callback(
    Output("tabela-detalhes-vec-os", "rowData"),
    [Input("store-dados-os", "data"), Input("input-lista-vec-detalhar", "value"), Input("input-dias", "value")],
)
def update_tabela_veiculos_detalhar(data, vec_detalhar, min_dias):
    if data["vazio"] or vec_detalhar is None or vec_detalhar == "":
        return []

    #####
    # Obtém os dados de retrabalho
    #####
    df_previous_services = pd.DataFrame(data["df_previous_services"])
    df_fixes = pd.DataFrame(data["df_fixes"])

    # Filtra as OS do veículo
    df_previous_services_vec = pd.DataFrame()
    if not df_previous_services.empty:
        df_previous_services_vec = df_previous_services[
            df_previous_services["CODIGO DO VEICULO"] == vec_detalhar
        ].copy()
        df_previous_services_vec["CLASSIFICACAO"] = "Retrabalho"
        df_previous_services_vec["CLASSIFICACAO_EMOJI"] = "❌"

    df_fixes_vec = pd.DataFrame()
    if not df_fixes.empty:
        df_fixes_vec = df_fixes[df_fixes["CODIGO DO VEICULO"] == vec_detalhar].copy()
        df_fixes_vec["CLASSIFICACAO"] = "Correção"
        df_fixes_vec["CLASSIFICACAO_EMOJI"] = "✅"

    # Junta os dados
    df_detalhar = pd.concat([df_previous_services_vec, df_fixes_vec])
    df_detalhar = df_detalhar.sort_values(by=["CODIGO DO VEICULO", "DATA_INICIO_SERVICO_DT"])

    # Formata datas
    df_detalhar["DIA_INICIO"] = pd.to_datetime(df_detalhar["DATA INICIO SERVICO"]).dt.strftime("%d/%m/%Y %H:%M")
    df_detalhar["DIA_TERMINO"] = pd.to_datetime(df_detalhar["DATA DE FECHAMENTO DO SERVICO"]).dt.strftime(
        "%d/%m/%Y %H:%M"
    )

    # Computa DIFF
    # df_detalhar["DIFF_DAYS"] = pd.to_datetime(df_detalhar["DATA INICIO SERVICO"]).diff().dt.days
    # df_detalhar["DIFF_DAYS"] = df_detalhar["DIFF_DAYS"].fillna(0)
    # df_detalhar["DIFF_DAYS"] = df_detalhar["DIFF_DAYS"].astype(int)

    # Remove campos -1 em DIAS_ATE_OS_CORRIGIR', 'NUM_OS_ATE_OS_CORRIGIR'
    df_detalhar = df_detalhar.replace(-1, "-")

    # Encontra o colaborador
    for ix, linha in df_detalhar.iterrows():
        colaborador = linha["COLABORADOR QUE EXECUTOU O SERVICO"]
        nome_colaborador = "Não encontrado"
        if colaborador in df_mecanicos["cod_colaborador"].values:
            nome_colaborador = df_mecanicos[df_mecanicos["cod_colaborador"] == colaborador]["nome_colaborador"].values[
                0
            ]
            nome_colaborador = re.sub(r"(?<!^)([A-Z])", r" \1", nome_colaborador)

        df_detalhar.at[ix, "LABEL_COLABORADOR"] = f"{colaborador} - {nome_colaborador}"

    # df_merge = df_detalhar.merge(df_mecanicos, left_on="COLABORADOR QUE EXECUTOU O SERVICO", right_on="cod_colaborador")

    return df_detalhar.to_dict("records")
