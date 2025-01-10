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

# Tabela Top OS de Retrabalho
tbl_top_os_geral_retrabalho = [
    {"field": "DESCRICAO DA OFICINA", "headerName": "OFICINA", "filter": "agSetColumnFilter", "minWidth": 200},
    {"field": "DESCRICAO DA SECAO", "headerName": "SEÇÃO", "filter": "agSetColumnFilter", "minWidth": 200},
    {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "filter": "agSetColumnFilter", "minWidth": 250},
    {
        "field": "TOTAL_OS",
        "headerName": "TOTAL DE OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 160,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% RETRABALHOS",
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORREÇÕES DE PRIMEIRA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "TOTAL_PROBLEMA",
        "headerName": "TOTAL DE PROBLEMA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "type": ["numericColumn"],
    },
    {
        "field": "REL_OS_PROBLEMA",
        "headerName": "REL OS/PROBLEMA",
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
dash.register_page(__name__, name="Visão Geral", path="/", icon="mdi:bus-alert")

##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Cabeçalho
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:bus-alert", width=45), width="auto"),
                dbc.Col(html.H1("Visão geral do retrabalho", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        html.Hr(),
        # Inputs
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
        dmc.Space(h=10),
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
                                    dbc.Label("Seções (categorias) de manutenção"),
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
        dmc.Space(h=10),
        dbc.Card(
            [
                html.Div(
                    [
                        dbc.Label("Ordens de Serviço"),
                        dcc.Dropdown(
                            id="input-select-ordens-servico-visao-geral",
                            options=[{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_todas_os],
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
        # # Gráfico de pizza com a relação entre Retrabalho e Correção
        # dmc.Space(h=30),
        # dbc.Row(
        #     [
        #         dbc.Col(DashIconify(icon="fluent:arrow-rotate-clockwise-24-filled", width=45), width="auto"),
        #         dbc.Col(html.H4("Síntese", className="align-self-center"), width=True),
        #     ],
        #     align="center",
        # ),
        # Graficos de Evolução do Retrabalho por Garagem e Seção
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Evolução do retrabalho por oficina / mês", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-garagem-por-mes"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Evolução do retrabalho por seção / mês", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-secao-por-mes"),
        dmc.Space(h=40),
        # Tabela com as estatísticas gerais de Retrabalho
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:line-horizontal-4-search-16-filled", width=45), width="auto"),
                dbc.Col(html.H4("Detalhamento por tipo de OS (serviço)", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            # enableEnterpriseModules=True,
            id="tabela-top-os-retrabalho-geral",
            columnDefs=tbl_top_os_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
        ),
        dmc.Space(h=40),
        # Tabela com as estatísticas gerais por Colaborador
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:account-wrench", width=45), width="auto"),
                dbc.Col(
                    html.H4("Detalhamento por colaborador das OSs escolhidas", className="align-self-center"),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-top-os-colaborador-geral",
            columnDefs=tbl_top_colaborador_geral_retrabalho,
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


# Corrige o input para garantir que "TODAS" não seja selecionado junto com outras opções
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


@callback(
    Output("input-select-oficina-visao-geral", "value"),
    Input("input-select-oficina-visao-geral", "value"),
)
def corrige_input_oficina(lista_oficinas):
    return corrige_input(lista_oficinas)


@callback(
    Output("input-select-secao-visao-geral", "value"),
    Input("input-select-secao-visao-geral", "value"),
)
def corrige_input_secao(lista_secaos):
    return corrige_input(lista_secaos)


@callback(
    [
        Output("input-select-ordens-servico-visao-geral", "options"),
        Output("input-select-ordens-servico-visao-geral", "value"),
    ],
    [
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
    ],
)
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


# Callbacks para o grafico de evolução do retrabalho por oficina
@callback(
    Output("graph-evolucao-retrabalho-por-garagem-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_oficina_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
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
        "DESCRICAO DA OFICINA",
        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
    FROM
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {subquery_oficinas_str}
        {subquery_secoes_str}
        {subquery_os_str}
    GROUP BY
        year_month, "DESCRICAO DA OFICINA"
    ORDER BY
        year_month;
    """

    # Executa query
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


# Callbacks para o grafico de evolução do retrabalho por seção
@callback(
    Output("graph-evolucao-retrabalho-por-secao-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
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
                text="Retrabalho por seção (% das OS)",
                x=0.25,  # Posição X para o primeiro plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de primeira por seção (% das OS)",
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

    # fig.update_layout(
    #     height=400,  # Define a altura do gráfico
    # )

    return fig


@callback(
    Output("tabela-top-os-retrabalho-geral", "rowData"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def atualiza_tabela_top_os_geral_retrabalho(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
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

    inner_subquery_oficinas_str = subquery_oficinas(lista_oficinas, "main.")
    inner_subquery_secoes_str = subquery_secoes(lista_secaos, "main.")
    inner_subquery_os_str = subquery_os(lista_os, "main.")

    # query = f"""
    #     SELECT
    #         "DESCRICAO DA OFICINA",
    #         "DESCRICAO DA SECAO",
    #         "DESCRICAO DO SERVICO",
    #         COUNT(*) as "TOTAL_OS",
    #         100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
    #         100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
    #     FROM
    #         mat_view_retrabalho_{min_dias}_dias
    #     WHERE
    #         "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
    #         {subquery_oficinas_str}
    #         {subquery_secoes_str}
    #         {subquery_os_str}
    #     GROUP BY
    #         "DESCRICAO DA OFICINA", "DESCRICAO DA SECAO", "DESCRICAO DO SERVICO"
    #     ORDER BY
    #         "PERC_RETRABALHO" DESC;
    # """

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
        COALESCE(op.num_problema, 0) AS "TOTAL_PROBLEMA"
    FROM
        mat_view_retrabalho_{min_dias}_dias main
    LEFT JOIN
        os_problema op
    ON
        main."DESCRICAO DA OFICINA" = op."DESCRICAO DA OFICINA"
        AND main."DESCRICAO DA SECAO" = op."DESCRICAO DA SECAO"
        AND main."DESCRICAO DO SERVICO" = op.servico
    WHERE
        main."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {inner_subquery_oficinas_str}
        {inner_subquery_secoes_str}
        {inner_subquery_os_str}
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


@callback(
    Output("tabela-top-os-colaborador-geral", "rowData"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def atualiza_tabela_top_colaboradores_geral_retrabalho(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
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

    inner_subquery_oficinas_str = subquery_oficinas(lista_oficinas, "main.")
    inner_subquery_secoes_str = subquery_secoes(lista_secaos, "main.")
    inner_subquery_os_str = subquery_os(lista_os, "main.")

    # query = f"""
    #     SELECT
    #         "COLABORADOR QUE EXECUTOU O SERVICO",
    #         COUNT(*) as "TOTAL_OS",
    #         -- SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
    #         -- SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
    #         -- SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
    #         100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
    #         -- 100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
    #         100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
    #     FROM
    #         mat_view_retrabalho_{min_dias}_dias
    #     WHERE
    #         "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
    #         {subquery_oficinas_str}
    #         {subquery_secoes_str}
    #         {subquery_os_str}
    #     GROUP BY
    #         "COLABORADOR QUE EXECUTOU O SERVICO"
    #     ORDER BY
    #         "PERC_RETRABALHO" DESC;
    # """

    query = f"""
        WITH normaliza_problema AS (
            SELECT
                "COLABORADOR QUE EXECUTOU O SERVICO" AS colaborador,
                "DESCRICAO DO SERVICO",
                "CODIGO DO VEICULO",
                "problem_no"
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
            GROUP BY
                "COLABORADOR QUE EXECUTOU O SERVICO",
                "DESCRICAO DO SERVICO",
                "CODIGO DO VEICULO",
                "problem_no"
        ),
        colaborador_problema AS (
            SELECT 
                colaborador, 
                COUNT(*) AS num_problema
            FROM 
                normaliza_problema
            GROUP BY 
                colaborador
        )
        SELECT
            main."COLABORADOR QUE EXECUTOU O SERVICO",
            COUNT(*) AS "TOTAL_OS",
            SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            COALESCE(cp.num_problema, 0) AS "TOTAL_PROBLEMA"
        FROM
            mat_view_retrabalho_{min_dias}_dias main
        LEFT JOIN
            colaborador_problema cp
            ON
            main."COLABORADOR QUE EXECUTOU O SERVICO" = cp.colaborador
        WHERE
            main."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {inner_subquery_oficinas_str}
            {inner_subquery_secoes_str}
            {inner_subquery_os_str}
        GROUP BY
            main."COLABORADOR QUE EXECUTOU O SERVICO",
            cp.num_problema
        ORDER BY
            "PERC_RETRABALHO" DESC;
    """

    # Executa Query
    df = pd.read_sql(query, pgEngine)

    df["REL_OS_PROBLEMA"] = round(df["TOTAL_OS"] / df["TOTAL_PROBLEMA"], 2)

    # Adiciona label de nomes
    df["COLABORADOR QUE EXECUTOU O SERVICO"] = df["COLABORADOR QUE EXECUTOU O SERVICO"].astype(int)

    # Encontra o nome do colaborador
    for ix, linha in df.iterrows():
        colaborador = linha["COLABORADOR QUE EXECUTOU O SERVICO"]
        nome_colaborador = "Não encontrado"
        if colaborador in df_mecanicos["cod_colaborador"].values:
            nome_colaborador = df_mecanicos[df_mecanicos["cod_colaborador"] == colaborador]["nome_colaborador"].values[
                0
            ]
            nome_colaborador = re.sub(r"(?<!^)([A-Z])", r" \1", nome_colaborador)

        df.at[ix, "LABEL_COLABORADOR"] = f"{nome_colaborador} - {int(colaborador)}"
        df.at[ix, "NOME_COLABORADOR"] = f"{nome_colaborador}"
        df.at[ix, "ID_COLABORADOR"] = int(colaborador)

    return df.to_dict("records")
