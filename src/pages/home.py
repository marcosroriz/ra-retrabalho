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
dash.register_page(__name__, path="/", icon="mdi:bus-alert")

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
                dbc.Col(DashIconify(icon="mdi:bus-alert", width=45), width="auto"),
                dbc.Col(html.H1("Visão Geral das OSs", className="align-self-center"), width=True),
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
        dcc.Store(id="store-dados-geral-os"),
        dbc.Row(dmc.Space(h=10)),
        # Conteúdo
        html.Hr(),
        dbc.Row(dmc.Space(h=10)),
        dbc.Row(dmc.Space(h=10)),
        dbc.Row(
            [
                html.H4("Evolução do Retrabalho de OS por Seção / Mês"),
                dcc.Graph(id="graph-evolucao-retrabalho-os-secao-por-mes"),
            ]
        ),
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

# @callback(
#     Output("store-dados-geral-os", "data"),
#     [
#         Input("input-lista-os", "value"),
#         Input("input-intervalo-datas", "value"),
#         Input("input-dias", "value"),
#     ],
#     running=[(Output("loading-overlay", "visible"), True, False)],
# )
# def computa_retrabalho(lista_os, datas, min_dias):
#     dados_vazios = {
#         "df_os": pd.DataFrame().to_dict("records"),
#         "df_estatistica": pd.DataFrame().to_dict("records"),
#         "df_retrabalho": pd.DataFrame().to_dict("records"),
#         "df_correcao": pd.DataFrame().to_dict("records"),
#         "df_correcao_primeira": pd.DataFrame().to_dict("records"),
#         "df_modelo": pd.DataFrame().to_dict("records"),
#         "df_colaborador": pd.DataFrame().to_dict("records"),
#         "df_dias_para_correcao": pd.DataFrame().to_dict("records"),
#         "df_num_os_por_problema": pd.DataFrame().to_dict("records"),
#         "vazio": True,
#     }


@callback(
    Output("graph-evolucao-retrabalho-os-secao-por-mes", "figure"),
    Input("input-intervalo-datas", "value"),
    running=[(Output("loading-overlay", "visible"), True, False)],
)
def plota_grafico_evolucao_retrabalho_os_por_mes(datas):
    if datas is None or not datas or None in datas:
        return go.Figure()

    query = """
    SELECT  
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        "DESCRICAO DA SECAO",
        COUNT(*) as "TOTAL_OS",
        SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
        SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
        SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
	    ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 2) AS "PERC_RETRABALHO",
	    ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 2) AS "PERC_CORRECAO",
	    ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 2) AS "PERC_CORRECAO_PRIMEIRA"
	FROM 
        mat_view_retrabalho_10_dias
    GROUP BY 
        year_month, "DESCRICAO DA SECAO"
    ORDER BY 
        year_month;
    """

    df = pd.read_sql(query, pgEngine)

    # Arruma dt
    df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

    # Cores
    # color_map = {"Não definido": "#1F77B4", "Amarelo": "#EECA3B", "Vermelho": "#D62728", "Verde": "#2CA02C"}

    # Gera o gráfico
    fig = px.line(
        df,
        x="year_month_dt",
        y="PERC_RETRABALHO",
        color="DESCRICAO DA SECAO",
        labels={"month_year_dt": "Ano-Mês", "count": "# OS"},
        markers=True,
    )

    # Coloca % no eixo y
    fig.update_yaxes(tickformat=".0%", title="% Retrabalho (Total de OS)")

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês")

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
                        "true" if filter_value == "TODAS" else f"params.data.'DESCRICAO DA SECAO' == '{filter_value}'"
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
