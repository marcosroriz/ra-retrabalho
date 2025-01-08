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


##############################################################################
# Obtêm os dados dos colaboradores
##############################################################################
# Obtem os dados dos mecânicos informados pela RA
df_mecanicos = pd.read_sql(
    """
    SELECT * FROM colaboradores_frotas_os
    """,
    pgEngine,
)

# Ajusta espaços no nome do colaborador
df_mecanicos["LABEL_COLABORADOR"] = df_mecanicos["nome_colaborador"].apply(
    lambda x: re.sub(r"(?<!^)([A-Z])", r" \1", x)
)

# Obtêm os dados de todos os mecânicos que trabalharam na RA, mesmo os desligados
df_mecanicos_todos = pd.read_sql(
    """
    SELECT DISTINCT "COLABORADOR QUE EXECUTOU O SERVICO" 
    FROM os_dados od 
    """,
    pgEngine,
)

# Converte cod_colaborador para int
df_mecanicos_todos["cod_colaborador"] = df_mecanicos_todos["COLABORADOR QUE EXECUTOU O SERVICO"].astype(int)

# Faz merge dos dados dos mecânicos da RA com os dados de todos os mecânicos
df_mecanicos_todos = df_mecanicos_todos.merge(df_mecanicos, how="left", on="cod_colaborador")

# Adiciona o campo não informados para os colaboradores que não estão na RA
df_mecanicos_todos["LABEL_COLABORADOR"] = df_mecanicos_todos["LABEL_COLABORADOR"].fillna("Não Informado")

# Adiciona o campo "cod_colaborador" para o campo LABEL
df_mecanicos_todos["LABEL_COLABORADOR"] = (
    df_mecanicos_todos["LABEL_COLABORADOR"] + " (" + df_mecanicos_todos["cod_colaborador"].astype(str) + ")"
)

# Ordena os colaboradores
df_mecanicos_todos = df_mecanicos_todos.sort_values("LABEL_COLABORADOR")


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(
    __name__, name="Retrabalho por Colaborador", path="/retrabalho-por-colaborador", icon="fluent-mdl2:timeline"
)

##############################################################################
layout = dbc.Container(
    [
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


def obtem_dados_os_mecanico(id_mecanico):
    # Query
    query = f"""
        SELECT * 
        FROM os_dados od
        WHERE od."COLABORADOR QUE EXECUTOU O SERVICO" = {id_mecanico}
    """
    df_os_mecanico_query = pd.read_sql_query(query, pgEngine)

    # Tratamento de datas
    df_os_mecanico_query["DATA INICIO SERVICO"] = pd.to_datetime(df_os_mecanico_query["DATA INICIO SERVIÇO"])
    df_os_mecanico_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(
        df_os_mecanico_query["DATA DE FECHAMENTO DO SERVICO"]
    )

    return df_os_mecanico_query


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
    df_os_mecanico = obtem_dados_os_mecanico(id_colaborador)

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
