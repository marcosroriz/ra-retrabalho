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
    pgEngine
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
    pgEngine
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
    {"field": "DESCRICAO DA SECAO", "headerName": "SEÇÃO"},
    {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "minWidth": 200},
    {"field": "TOTAL_OS", "headerName": "# OS"},
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% RETRABALHOS",
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORRECOES PRIMEIRA",
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
                dbc.Col(html.H1("Visão Geral das OSs",
                        className="align-self-center"), width=True),
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
                                    dbc.Label(
                                        "Tempo entre OS (em dias) para ser considerado retrabalho"
                                    ),
                                    dcc.Dropdown(
                                        id="input-select-dias-geral-retrabalho",
                                        options=[
                                            {"label": "10 dias", "value": 10},
                                            {"label": "15 dias", "value": 15},
                                            {"label": "30 dias", "value": 30}
                                        ],
                                        placeholder="Período em dias",
                                        value=10
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
        html.Hr(),
        # Evolução do Retrabalho
        dmc.LineChart(
            id="dmc-chart",
            h=300,
            dataKey="date",
            data=[],
            series=[],
            curveType="linear",
            tickLine="xy",
            withXAxis=False,
            withDots=False,
        ),
        dbc.Row(dmc.Space(h=10)),
        dbc.Row(
            [
                html.H4("Retrabalho por Garagem / Mês"),
                dcc.Graph(id="graph-evolucao-retrabalho-por-garagem-por-mes"),
            ]
        ),
        dbc.Row(
            [
                html.H4("Retrabalho por Seção / Mês"),
                dcc.Graph(id="graph-evolucao-retrabalho-por-secao-por-mes"),
            ]
        ),
        # dbc.Row(
        #     [
        #         dbc.Col(
        #             dbc.Row(
        #                 [
        #                     html.H4("Retrabalho por Garagem / Mês"),
        #                     dcc.Graph(id="graph-evolucao-retrabalho-por-garagem-por-mes"),
        #                 ]
        #             ),
        #             md=6
        #         ),
        #         dbc.Col(
        #             dbc.Row(
        #                 [
        #                     html.H4("Retrabalho por Seção / Mês"),
        #                     dcc.Graph(id="graph-evolucao-retrabalho-por-secao-por-mes"),
        #                 ]
        #             ),
        #             md=6
        #         )
        #     ]
        # ),
        # Tabela com as estatísticas gerais de Retrabalho de OS por Seção
        html.Hr(),
        html.H4("Top OS de Retrabalho Geral"),
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
                                                "label": linha["label"],
                                                "value": linha["value"],
                                            }
                                            for linha in data_filtro_top_os_geral_retrabalho
                                        ],
                                        value=["TODAS"],
                                        multi=True,
                                        placeholder="Selecione uma ou mais seções",
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
        dmc.RadioGroup(
            children=dmc.Group(
                [dmc.Radio(opt["label"], value=opt["value"]) for opt in data_filtro_top_os_geral_retrabalho], my=10
            ),
            id="radiogroup-simple",
            value="react",
            label="Selecione a Seção para Filtrar",
            size="sm",
            mb=10,
        ),
        dbc.RadioItems(
            options=[
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
            ],
            value="TODAS",
            id="radio-filtro-top-os-retrabalho-geral",
            inline=True,
        ),
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
    ]
)


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

@callback(
    Output("store-dados-geral-os", "data"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
    ],
)
def computa_retrabalho(datas, min_dias):
    dados_vazios = {
        "df_agg_oficina": pd.DataFrame().to_dict("records"),
        "vazio": True,
    }

    if datas is None or not datas or None in datas or min_dias is None:
        return dados_vazios

    return dados_vazios

@callback(
    [
        Output("dmc-chart", "data"),
        Output("dmc-chart", "series"),
    ],
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
    ]
)
def plota_dmc(datas, min_dias):
    if datas is None or not datas or None in datas or min_dias is None:
        return [], []

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        "DESCRICAO DA OFICINA",
        ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 2) AS "PERC_RETRABALHO"
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
    df["year_month_dt"] = pd.to_datetime(
        df["year_month"], format="%Y-%m", errors="coerce")


@callback(
    Output("graph-evolucao-retrabalho-por-garagem-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
    ]
)
def plota_grafico_evolucao_retrabalho_por_oficina_por_mes(datas, min_dias):
    if datas is None or not datas or None in datas or min_dias is None:
        return go.Figure()

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        "DESCRICAO DA OFICINA",
        ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 2) AS "PERC_RETRABALHO"
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
    df["year_month_dt"] = pd.to_datetime(
        df["year_month"], format="%Y-%m", errors="coerce")

    # Cores

    # Gera o gráfico
    fig = px.line(
        df,
        x="year_month_dt",
        y="PERC_RETRABALHO",
        color="DESCRICAO DA OFICINA",
        labels={"DESCRICAO DA OFICINA": "Oficina", "year_month_dt": "Ano-Mês", "PERC_RETRABALHO": "% Retrabalho"},
        markers=True,
    )

    # Coloca % no eixo y
    fig.update_yaxes(tickformat=".0%", title="% Retrabalho (Total de OS)")

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês")

    fig.update_layout(
        height=400,  # Define a altura do gráfico
    )

    return fig


@callback(
    Output("graph-evolucao-retrabalho-por-secao-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
    ]
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(datas, min_dias):
    if datas is None or not datas or None in datas or min_dias is None:
        return go.Figure()

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        "DESCRICAO DA SECAO",
        ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 2) AS "PERC_RETRABALHO"
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
    df["year_month_dt"] = pd.to_datetime(
        df["year_month"], format="%Y-%m", errors="coerce")

    # Gera o gráfico
    fig = px.line(
        df,
        x="year_month_dt",
        y="PERC_RETRABALHO",
        color="DESCRICAO DA SECAO",
        labels={"DESCRICAO DA SECAO": "Seção", "year_month_dt": "Ano-Mês", "PERC_RETRABALHO": "% Retrabalho"},
        markers=True,
    )

    # Coloca % no eixo y
    fig.update_yaxes(tickformat=".0%", title="% Retrabalho (Total de OS)")

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês")

    fig.update_layout(
        # legend=dict(
        #     orientation="h",
        #     yanchor="bottom",
        #     y=-1.02,
        #     xanchor="right",
        #     x=1,
        #     title=None
        # ),
        height=400,  # Define a altura do gráfico
    )
    # fig.update_layout(
    #     legend_x=0,
    #     legend_y=0
    # )
    return fig


filtro_tabela_top_os_geral_retrabalho = {
    "below25": "params.data['DESCRICAO DA SECAO'] == 25",
    "between25and50": "params.data.age >= 25 && params.data.age <= 50",
    "above50": "params.data.age > 50",
    "dateAfter2008": "dateAfter2008(params)",
    "everyone": "true",
}


@callback(
    Output("tabela-top-os-retrabalho-geral", "dashGridOptions"),
    Input("radio-filtro-top-os-retrabalho-geral", "value"),
    prevent_initial_call=True,
)
def atualiza_filtro_tabela_top_os_geral_retrabalho(filter_value):
    import json

    print(
        json.dumps(
            {
                "isExternalFilterPresent": {"function": "true" if filter_value != "TODAS" else "false"},
                "doesExternalFilterPass": {
                    "function": (
                        "true" if filter_value == "TODAS" else f"params.data.'DESCRICAO DA SECAO' == '{
                            filter_value}'"
                    )
                },
            }
        )
    )
    return {
        # if filter_value is not 'everyone', then we are filtering
        "isExternalFilterPresent": {"function": "true" if filter_value != "TODAS" else "false"},
        "doesExternalFilterPass": {
            "function": "true" if filter_value == "TODAS" else f"params.data['DESCRICAO DA SECAO'] == '{filter_value}'"
        },
    }


@callback(Output("tabela-top-os-retrabalho-geral", "rowData"), Input("input-intervalo-datas", "value"))
def atualiza_tabela_top_os_geral_retrabalho(datas):
    if datas is None or not datas or None in datas:
        return []

    query = """
        SELECT
	        "DESCRICAO DA SECAO",
            "DESCRICAO DO SERVICO",
            COUNT(*) as "TOTAL_OS",
            SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
	        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 2) AS "PERC_RETRABALHO",
	        100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 2) AS "PERC_CORRECAO",
	        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 2) AS "PERC_CORRECAO_PRIMEIRA"
        FROM 
            mat_view_retrabalho_30_dias
        GROUP BY 
            "DESCRICAO DA SECAO", "DESCRICAO DO SERVICO"
        ORDER BY 
            "PERC_RETRABALHO" DESC;
    """

    df = pd.read_sql(query, pgEngine)
    return df.to_dict("records")
