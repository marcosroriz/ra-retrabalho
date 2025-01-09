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

# Obtem as Oficinas
df_oficinas_pg = pd.read_sql(
    """
    SELECT 
        DISTINCT "DESCRICAO DA OFICINA"
    FROM 
        mat_view_retrabalho_10_dias mvrd 
    ORDER BY 
        "DESCRICAO DA OFICINA"
    """,
    pgEngine,
)

# Seções
df_secoes_pg = pd.read_sql(
    """
    SELECT DISTINCT
        "DESCRICAO DA SECAO"
    FROM 
        mat_view_retrabalho_10_dias mvrd 
    ORDER BY
        "DESCRICAO DA SECAO"
    """,
    pgEngine,
)


# Tabela Top OS de Retrabalho
data_filtro_top_os_geral_retrabalho = [
    {"label": "Todas as Seções", "value": "TODAS"},
    {"label": "Alinhamento", "value": "SETOR DE ALINHAMENTO"},
    {"label": "Borracharia", "value": "MANUTENCAO BORRACHARIA"},
    {"label": "Elétrica", "value": "MANUTENCAO ELETRICA"},
    {"label": "Garagem", "value": "MANUTENÇÃO GARAGEM"},
    {"label": "Mecânica", "value": "MANUTENCAO MECANICA"},
    {"label": "Lanternagem", "value": "MANUTENCAO LANTERNAGEM"},
    {"label": "Lubrificação", "value": "LUBRIFICAÇÃO"},
    {"label": "Pintura", "value": "MANUTENCAO PINTURA"},
    {"label": "Polimentos", "value": "SETOR DE POLIMENTO"},
    {"label": "Terceiros", "value": "SERVIÇOS DE TERCEIROS"},
]


tbl_top_os_geral_retrabalho = [
    {"field": "DESCRICAO DA OFICINA", "headerName": "OFICINA", "minWidth": 200},
    {"field": "DESCRICAO DA SECAO", "headerName": "SEÇÃO"},
    {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "minWidth": 200},
    {"field": "TOTAL_OS", "headerName": "TOTAL DE OS", "maxWidth": 150, "type": ["numericColumn"]},
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% RETRABALHOS",
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORRECOES PRIMEIRA",  # Long header text for testing wrapping
        "wrapHeaderText": True,  # Enable text wrapping for this column
        "autoHeaderHeight": True,  # Automatically adjust height if needed
        "maxWidth": 150,
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
]


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Visão Geral", path="/", icon="mdi:bus-alert")

##############################################################################
layout = dbc.Container(
    [
        # Cabeçalho
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:bus-alert", width=45), width="auto"),
                dbc.Col(html.H1("Visão Geral do Retrabalho", className="align-self-center"), width=True),
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
                                    dbc.Label("Tempo entre OS (em dias) para ser considerado retrabalho"),
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
            ]
        ),
        dbc.Row(dmc.Space(h=10)),
        dbc.Row(
            [
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
                                            {"label": "GARAGEM CENTRAL", "value": "GARAGEM CENTRAL - RAL"},
                                            {"label": "GARAGEM NOROESTE", "value": "GARAGEM NOROESTE - RAL"},
                                            {"label": "GARAGEM SUL", "value": "GARAGEM SUL - RAL"},
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
                                    dbc.Label("Seções (Categorias) de Manutenção"),
                                    dcc.Dropdown(
                                        id="input-select-secao-visao-geral",
                                        options=[
                                            {"label": "TODAS", "value": "TODAS"},
                                            {"label": "BORRACHARIA", "value": "MANUTENCAO BORRACHARIA"},
                                            {"label": "ELETRICA", "value": "MANUTENCAO ELETRICA"},
                                            {"label": "GARAGEM", "value": "MANUTENÇÃO GARAGEM"},
                                            {"label": "LANTERNAGEM", "value": "MANUTENCAO LANTERNAGEM"},
                                            {"label": "LUBRIFICAÇÃO", "value": "LUBRIFICAÇÃO"},
                                            {"label": "MECANICA", "value": "MANUTENCAO MECANICA"},
                                            {"label": "PINTURA", "value": "MANUTENCAO PINTURA"},
                                            {"label": "SERVIÇOS DE TERCEIROS", "value": "SERVIÇOS DE TERCEIROS"},
                                            {"label": "SETOR DE ALINHAMENTO", "value": "SETOR DE ALINHAMENTO"},
                                            {"label": "SETOR DE POLIMENTO", "value": "SETOR DE POLIMENTO"},
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
            ]
        ),
        dcc.Store(id="store-dados-geral-os"),
        dbc.Row(dmc.Space(h=10)),
        # Conteúdo
        dmc.Space(h=10),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Evolução por Oficina / Mês", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        # html.H4("Retrabalho e Correção de Primeira por Oficina / Mês"),
        dcc.Graph(id="graph-evolucao-retrabalho-por-garagem-por-mes"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Evolução por Seção / Mês", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        # html.H4("Retrabalho e Correção de Primeira por Seção / Mês"),
        dcc.Graph(id="graph-evolucao-retrabalho-por-secao-por-mes"),
        dmc.Space(h=20),
        # Tabela com as estatísticas gerais de Retrabalho
        html.Hr(),
        dmc.Space(h=20),
        html.H4("Detalhamento do Retrabalho"),
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-top-os-retrabalho-geral",
            columnDefs=tbl_top_os_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="responsiveSizeToFit",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
        ),
        dmc.Space(h=40),
        # Tabela com as estatísticas gerais por Colaborador
        html.Hr(),
        dmc.Space(h=20),
        html.H4("Detalhamento do Colaborador"),
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-top-os-colaborador-geral",
            columnDefs=tbl_top_os_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="responsiveSizeToFit",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
        ),
        dmc.Space(h=40),
    ]
)


##############################################################################
# CALLBACKS ##################################################################
##############################################################################


@callback(
    Output("store-dados-geral-os", "data"),
    [Input("input-intervalo-datas-geral", "value"), Input("input-select-dias-geral-retrabalho", "value")],
)
def computa_retrabalho(datas, min_dias):
    dados_vazios = {
        "df_agg_oficina": pd.DataFrame().to_dict("records"),
        "vazio": True,
    }

    if datas is None or not datas or None in datas or min_dias is None:
        return dados_vazios

    return dados_vazios


# @callback(
#     [
#         Output("dmc-chart", "data"),
#         Output("dmc-chart", "series"),
#     ],
#     [
#         Input("input-intervalo-datas-geral", "value"),
#         Input("input-select-dias-geral-retrabalho", "value"),
#     ],
# )
# def plota_dmc(datas, min_dias):
#     if datas is None or not datas or None in datas or min_dias is None:
#         return [], []

#     query = f"""
#     SELECT
#         to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
#         "DESCRICAO DA OFICINA",
#         ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 2) AS "PERC_RETRABALHO"
#     FROM
#         mat_view_retrabalho_{min_dias}_dias
#     WHERE
#         "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{datas[0]}' AND '{datas[1]}'
#     GROUP BY
#         year_month, "DESCRICAO DA OFICINA"
#     ORDER BY
#         year_month;
#     """

#     df = pd.read_sql(query, pgEngine)

#     # Arruma dt
#     df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")


@callback(
    Output("graph-evolucao-retrabalho-por-garagem-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_oficina_por_mes(datas, min_dias):
    if datas is None or not datas or None in datas or min_dias is None:
        return go.Figure()

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        "DESCRICAO DA OFICINA",
        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
    FROM
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{datas[0]}' AND '{datas[1]}'
    GROUP BY
        year_month, "DESCRICAO DA OFICINA"
    ORDER BY
        year_month;
    """

    df = pd.read_sql(query, pgEngine)

    # Arruma dt
    df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

    # Funde (melt) colunas de retrabalho e correção
    df_combinado = df.melt(
        id_vars=["year_month_dt", "DESCRICAO DA OFICINA"],
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

    # Gera o gráfico
    fig = px.line(
        df_combinado,
        x="year_month_dt",
        y="PERC",
        color="DESCRICAO DA OFICINA",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"DESCRICAO DA OFICINA": "Oficina", "year_month_dt": "Ano-Mês", "PERC": "%"},
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
                text="Retrabalho por Garagem (% das OS)",
                x=0.25,  # X position for the first subplot title
                y=1.05,  # Y position (above the plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de Primeira por Garagem (% das OS)",
                x=0.75,  # X position for the second subplot title
                y=1.05,  # Y position (above the plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
        ]
    )

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês", title_standoff=90)

    # Adjust the standoff for each X-axis title
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))  # Increase standoff for spacing

    # fig.update_layout(
    #     height=400,  # Define a altura do gráfico
    # )

    return fig


@callback(
    Output("graph-evolucao-retrabalho-por-secao-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(datas, min_dias):
    if datas is None or not datas or None in datas or min_dias is None:
        return go.Figure()

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        "DESCRICAO DA SECAO",
        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
    FROM
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{datas[0]}' AND '{datas[1]}'
    GROUP BY
        year_month, "DESCRICAO DA SECAO"
    ORDER BY
        year_month;
    """

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

    # Gera o gráfico
    fig = px.line(
        df_combinado,
        x="year_month_dt",
        y="PERC",
        color="DESCRICAO DA SECAO",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"DESCRICAO DA SECAO": "Seção", "year_month_dt": "Ano-Mês", "PERC": "%"},
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
                text="Retrabalho por Seção (% das OS)",
                x=0.25,  # X position for the first subplot title
                y=1.05,  # Y position (above the plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de Primeira por Seção (% das OS)",
                x=0.75,  # X position for the second subplot title
                y=1.05,  # Y position (above the plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
        ]
    )

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês", title_standoff=90)

    # Adjust the standoff for each X-axis title
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))  # Increase standoff for spacing

    # fig.update_layout(
    #     height=400,  # Define a altura do gráfico
    # )

    return fig


@callback(Output("tabela-top-os-retrabalho-geral", "rowData"), Input("input-intervalo-datas-geral", "value"))
def atualiza_tabela_top_os_geral_retrabalho(datas):
    if datas is None or not datas or None in datas:
        return []

    query = """
        SELECT
            "DESCRICAO DA OFICINA",
	        "DESCRICAO DA SECAO",
            "DESCRICAO DO SERVICO",
            COUNT(*) as "TOTAL_OS",
            SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
	        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
	        100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
	        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
        FROM 
            mat_view_retrabalho_30_dias
        GROUP BY 
            "DESCRICAO DA OFICINA", "DESCRICAO DA SECAO", "DESCRICAO DO SERVICO"
        ORDER BY 
            "PERC_RETRABALHO" DESC;
    """

    df = pd.read_sql(query, pgEngine)

    print(df)
    return df.to_dict("records")
