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
                                                dmc.Title(id="indicador-quantidade-servico", order=2),
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
                                    dbc.CardFooter("Total de servicos realizados"),
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
                                                    id="indicador-total-os-trabalho",
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
                                    dbc.CardFooter("Total de OSs executadas"),
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
                                                    id="indicador-correcao-de-primeira",
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
                                    dbc.CardFooter("OSs com correção de primeira"),
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
                                                    id="indicador-teste",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="tabler:reorder",
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
                    ]
                ),
            ]
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

def obtem_dados_os_sql(id_colaborador, lista_os, data_inicio, data_fim, min_dias):
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
            AND od."COLABORADOR QUE EXECUTOU O SERVICO" = {id_colaborador}
            AND od."DESCRICAO DO SERVICO" IN ({', '.join([f"'{x}'" for x in lista_os])})
            -- AND (
                --"DESCRICAO DO SERVICO" = 'Motor cortando alimentação'
                --OR
                --"DESCRICAO DO SERVICO" = 'Motor sem força'
            --)
            --AND 
            --(
            --od."CODIGO DO VEICULO" ='50733'
            --OR
            --od."CODIGO DO VEICULO" ='50530'
            --)
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

    # print(query)
    df_os_query = pd.read_sql_query(query, pgEngine)

    # Tratamento de datas
    df_os_query["DATA INICIO SERVICO"] = pd.to_datetime(df_os_query["DATA INICIO SERVIÇO"])
    df_os_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(df_os_query["DATA DE FECHAMENTO DO SERVICO"])

    return df_os_query


def obtem_estatistica_retrabalho_sql(df_os, min_dias):
    # Lida com NaNs
    df_os = df_os.fillna(0)

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

        df_colaborador.at[ix, "LABEL_COLABORADOR"] = f"{nome_colaborador} - {int(colaborador)}"
        df_colaborador.at[ix, "NOME_COLABORADOR"] = f"{nome_colaborador}"
        df_colaborador.at[ix, "ID_COLABORADOR"] = int(colaborador)

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

    # Num de OS para correção
    df_num_os_por_problema = df_os.groupby(["problem_no", "CODIGO DO VEICULO"]).size().reset_index(name="TOTAL_DE_OS")

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
            "MEDIA_DE_OS_PARA_CORRECAO": df_num_os_por_problema["TOTAL_DE_OS"].mean(),
        },
        index=[0],
    )
     # Correções tardias
    df_estatistica["TOTAL_DE_CORRECOES_TARDIAS"] = (
        df_estatistica["TOTAL_DE_CORRECOES"] - df_estatistica["TOTAL_DE_CORRECOES_DE_PRIMEIRA"]
    )
    # Rel probl/os
    df_estatistica["RELACAO_OS_PROBLEMA"] = df_estatistica["TOTAL_DE_OS"] / df_estatistica["TOTAL_DE_PROBLEMAS"]

    # Porcentagens
    df_estatistica["PERC_RETRABALHO"] = 100 * (df_estatistica["TOTAL_DE_RETRABALHOS"] / df_estatistica["TOTAL_DE_OS"])
    df_estatistica["PERC_CORRECOES"] = 100 * (df_estatistica["TOTAL_DE_CORRECOES"] / df_estatistica["TOTAL_DE_OS"])
    df_estatistica["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (
        df_estatistica["TOTAL_DE_CORRECOES_DE_PRIMEIRA"] / df_estatistica["TOTAL_DE_OS"]
    )
    df_estatistica["PERC_CORRECOES_TARDIAS"] = 100 * (
        df_estatistica["TOTAL_DE_CORRECOES_TARDIAS"] / df_estatistica["TOTAL_DE_OS"]
    )
    
    return df_estatistica
    


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
    Output("indicador-total-os-trabalho", "children"),
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
    ],
)
def total_os_trabalhada(id_colaborador, datas):
    dados_vazios = {"df_os_mecanico": pd.DataFrame().to_dict("records"), "vazio": True}
   
    if not id_colaborador or not datas or len(datas) != 2 or None:
        return ''

    df_os_mecanico = obtem_dados_os_mecanico(id_colaborador)

    if df_os_mecanico.empty:
        return "Nenhuma OS encontrada para esse colaborador."

    
    inicio = pd.to_datetime(datas[0])
    fim = pd.to_datetime(datas[1])

    df_os_mecanico = df_os_mecanico[
        (df_os_mecanico["DATA INICIO SERVICO"] >= inicio) & (df_os_mecanico["DATA INICIO SERVICO"] <= fim)
    ]

    if df_os_mecanico.shape[0] == 0:
        return''
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

    df_os_mecanico = obtem_dados_os_mecanico(id_colaborador)

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

    df_os_mecanico = obtem_dados_os_mecanico(id_colaborador)
    
    df_os_analise = obtem_dados_os_sql(id_colaborador, df_os_mecanico['DESCRICAO DO SERVICO'].tolist(), inicio, fim, min_dias)
    
    df_relatorio = obtem_estatistica_retrabalho_sql(df_os_analise, min_dias)
    
    correcao = df_relatorio['PERC_CORRECOES_DE_PRIMEIRA'].astype(int).sum()

    
    return f"{str(correcao)}% correções de primeira"


###
####
@callback(
    Output("indicador-teste", "children"),
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

    df_os_mecanico = obtem_dados_os_mecanico(id_colaborador)
    
    df_os_analise = obtem_dados_os_sql(id_colaborador, df_os_mecanico['DESCRICAO DO SERVICO'].tolist(), inicio, fim, min_dias)
    
    df_relatorio = obtem_estatistica_retrabalho_sql(df_os_analise, min_dias)
    
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
