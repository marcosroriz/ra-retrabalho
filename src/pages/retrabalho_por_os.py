#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de uma ou mais OS

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import numpy as np
import pandas as pd
import sqlite3

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

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
con_banco_assets = sqlite3.connect(arq_utils.ARQUIVO_BANCO_ASSETS, check_same_thread=False)

# Dataframes básicos (veículos)
df_veiculos = pd.read_sql("SELECT * FROM veiculos", con_banco_assets)

# Dataframes básicos (OS)
df_os_servico = pd.read_sql_query("SELECT * FROM os_servico", con_banco_assets)

# Definir colunas da tabela de detalhamento
tbl_top10_os = [
    {"field": "DIA"},
    {"field": "NUMERO DA OS", "headerName": "OS"},
    {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO"},
    {"field": "DESCRICAO DO VEICULO", "headerName": "MODELO"},
    {"field": "DIAS_ATE_OS_CORRIGIR", "headerName": "DIAS"},
]

tbl_top10_vec = [
    {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO"},
    {"field": "TOTAL_DIAS_ATE_CORRIGIR", "headerName": "TOTAL DE DIAS GASTOS ATÉ CORRIGIR"},
]

tbl_detalhes_vec_os = [
    {"field": "NUMERO DA OS", "headerName": "OS", "maxWidth": 100},
    {"field": "CLASSIFICACAO_EMOJI", "headerName": "STATUS", "maxWidth": 150},
    {"field": "Nome", "headerName": "COLABORADOR"},
    {"field": "DIA_INICIO", "headerName": "INÍCIO", "maxWidth": 150},
    {"field": "DIA_TERMINO", "headerName": "FECHAMENTO", "maxWidth": 150},
    {"field": "DIFF_DAYS", "headerName": "DIFF DIAS", "maxWidth": 200},
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
                                            for ix, linha in df_os_servico.iterrows()
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
                                        maxDate=date(2024, 10, 8),
                                        value=[date(2024, 1, 1), date(2024, 10, 8)],
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
        dbc.Row(
            [
                # Gráfico de Pizza
                dbc.Col(dbc.Row([html.H4("Retrabalho x Correções"), dcc.Graph(id="graph-retrabalho-correcoes")]), md=6),
                # Indicadores
                dbc.Col(
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
                                                            dmc.Title(id="indicador-total-os", order=2),
                                                            DashIconify(
                                                                icon="material-symbols:order-approve-outline",
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
                                        md=6,
                                    ),
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
                                                                icon="codicon:error",
                                                                width=48,
                                                                color="black",
                                                            ),
                                                        ],
                                                        justify="space-around",
                                                        mt="md",
                                                        mb="xs",
                                                    ),
                                                ),
                                                dbc.CardFooter("% de Retrabalho"),
                                            ],
                                            id="card-media-selecionados-telemetria-planilha",
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
                                                dbc.CardFooter("Média de Dias até Correção"),
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
                                                dbc.CardFooter("Média de OS até Correção"),
                                            ],
                                            id="card-media-selecionados-telemetria-planilha",
                                            class_name="card-box-shadow",
                                        ),
                                        md=6,
                                    ),
                                ]
                            ),
                        ]
                    ),
                    md=6,
                ),
            ]
        ),
        # dbc.Row(dmc.Space(h=20)),
        dbc.Row([html.H4("Grafículo Cumulativo Dias para Correção"), dcc.Graph(id="graph-retrabalho-cumulativo")]),
        # dbc.Row(dmc.Space(h=20)),
        dbc.Row([html.H4("Retrabalho por Modelo"), dcc.Graph(id="graph-retrabalho-por-modelo")]),
        # TOP OS e Veículos
        html.Hr(),
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
                                id="tabela-top-10-os-problematicas",
                                columnDefs=tbl_top10_os,
                                rowData=[],
                                defaultColDef={"filter": True, "floatingFilter": True},
                                columnSize="responsiveSizeToFit",
                                # columnSize="sizeToFit",
                                # dashGridOptions={"pagination": True, "animateRows": False},
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
                                id="tabela-top-10-veiculos",
                                columnDefs=tbl_top10_vec,
                                rowData=[],
                                defaultColDef={"filter": True, "floatingFilter": True},
                                columnSize="responsiveSizeToFit",
                                # dashGridOptions={"pagination": True, "animateRows": False},
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
                    defaultColDef={"filter": True, "floatingFilter": True},
                    columnSize="autoSize",
                    # columnSize="sizeToFit",
                    # dashGridOptions={"pagination": True, "animateRows": False},
                ),
            ]
        ),
    ]
)


##############################################################################
# CALLBACKS ##################################################################
##############################################################################


def obtem_dados_os(lista_os):
    # Query
    query = f"""
        SELECT * FROM os 
        WHERE "DESCRICAO DO SERVICO" IN ({', '.join([f"'{x}'" for x in lista_os])})
    """
    df_os_query = pd.read_sql_query(query, con_banco_assets).copy()

    # Tratamento de datas
    df_os_query["DATA INICIO SERVICO"] = pd.to_datetime(df_os_query["DATA INICIO SERVICO"])
    df_os_query["DATA_INICIO_SERVICO_DT"] = pd.to_datetime(df_os_query["DATA_INICIO_SERVICO_DT"])
    df_os_query["DATA_FECHAMENTO_SERVICO_DT"] = pd.to_datetime(df_os_query["DATA_FECHAMENTO_SERVICO_DT"])

    return df_os_query


def obtem_estatistica_retrabalho(df_os, min_dias):
    # Ordena os dados
    df_os_ordenada = df_os.sort_values(
        by=["CODIGO DO VEICULO", "DESCRICAO DO SERVICO", "DATA_INICIO_SERVICO_DT"]
    ).copy()

    # Adicionando essa coluna para obter dias e num até corrigir
    df_os_ordenada["DIAS_ATE_OS_CORRIGIR"] = "-1"
    df_os_ordenada["NUM_OS_ATE_OS_CORRIGIR"] = "-1"

    # Df que agrupa por veículo e categoria
    grouped_df = df_os_ordenada.groupby(["CODIGO DO VEICULO", "DESCRICAO DO SERVICO"])

    # Inicializa os dataframes com resultados
    df_below_threshold = pd.DataFrame()  # Armazena OS abaixo do thresholdTo store orders below the threshold
    df_previous_services = pd.DataFrame()  # To store the immediate previous service orders
    df_fixes = pd.DataFrame()  # To store the previous service order when the current order exceeds the threshold

    # Loop em cada grupo
    for (codigo_veiculo, descricao_servico), group in grouped_df:
        # Ordena por dia
        group_df = group.sort_values(by="DATA_INICIO_SERVICO_DT").copy()

        # Calcula a diff in dias entre serviços consecutivos
        group_df["DIFF_DAYS"] = group_df["DATA INICIO SERVICO"].diff().dt.days

        # Lida com NaN
        group_df["DIFF_DAYS"] = group_df["DIFF_DAYS"].fillna(0)

        # Copia para evitar warnings
        df_veiculo_sorted = group_df.copy()

        # Inicio dos dados adicionais (tempo e dias até correção)
        row_inicio_do_problema = df_veiculo_sorted.iloc[0]
        num_os_ate_corrigir = 0

        # Se só tem um dado, então não tem retrabalho
        if len(df_veiculo_sorted) == 1:
            df_veiculo_sorted["DIAS_ATE_OS_CORRIGIR"] = 0
            df_veiculo_sorted["NUM_OS_ATE_OS_CORRIGIR"] = 0

            # Adiciona a df_fixes
            df_fixes = pd.concat([df_fixes, df_veiculo_sorted])
            continue

        # Faz o loop para calcular serviços consecutivos
        for i in range(1, len(df_veiculo_sorted)):  # Inicia da segunda linha para ter o dado anterior
            current_row = df_veiculo_sorted.iloc[i].copy()
            prev_row = df_veiculo_sorted.iloc[i - 1].copy()

            # Verifica se o DIFF_DAY da linha atual é menor que o intervalo
            if current_row["DIFF_DAYS"] <= min_dias:
                # Adiciona no df abaixo do intervalo
                df_below_threshold = pd.concat([df_below_threshold, current_row.to_frame().T])

                # Adicione a linha anteiror ao retrabalho
                df_previous_services = pd.concat([df_previous_services, prev_row.to_frame().T])

                # Incrementa o Num de OS até corrigir
                num_os_ate_corrigir = num_os_ate_corrigir + 1
            else:
                # Calcula a diferença em dias entre row_inicio_do_problema e current_row
                dia_inicio_problema = row_inicio_do_problema["DATA_INICIO_SERVICO_DT"]
                dia_inicio_correcao = prev_row["DATA_INICIO_SERVICO_DT"]
                diferenca_dias = (dia_inicio_correcao - dia_inicio_problema).days

                # Adiciona dados de tempo e numero de OS até correção
                prev_row["DIAS_ATE_OS_CORRIGIR"] = diferenca_dias
                prev_row["NUM_OS_ATE_OS_CORRIGIR"] = num_os_ate_corrigir

                # Adiciona a prev_row como correção, uma vez que > min_dias
                df_fixes = pd.concat([df_fixes, prev_row.to_frame().T])

                # Reseta linha atual como inicio do novo problema
                row_inicio_do_problema = current_row
                num_os_ate_corrigir = 0

            # Verifica se é a última linha
            if i == len(df_veiculo_sorted) - 1:
                # Calcula a diferença em dias entre row_inicio_do_problema e current_row
                dia_inicio_problema = row_inicio_do_problema["DATA_INICIO_SERVICO_DT"]
                dia_inicio_correcao = current_row["DATA_INICIO_SERVICO_DT"]
                diferenca_dias = (dia_inicio_correcao - dia_inicio_problema).days

                # Adiciona dados de tempo e numero de OS até correção
                current_row["DIAS_ATE_OS_CORRIGIR"] = diferenca_dias
                current_row["NUM_OS_ATE_OS_CORRIGIR"] = num_os_ate_corrigir

                # Adiciona ao df_fixes
                df_fixes = pd.concat([df_fixes, current_row.to_frame().T])
                break

    # Remove duplicados e reseta os indexes
    df_below_threshold = df_below_threshold.drop_duplicates().reset_index(drop=True)
    df_previous_services = df_previous_services.drop_duplicates().reset_index(drop=True)
    df_fixes = df_fixes.drop_duplicates().reset_index(drop=True)

    # Obtem estatisticas de cada DF
    df_os_agg = df_os_ordenada.groupby("DESCRICAO DO SERVICO").size().reset_index(name="TOTAL_DE_OS")
    df_fixes_agg = df_fixes.groupby("DESCRICAO DO SERVICO").size().reset_index(name="CORRECOES")
    df_previous_services_agg = (
        df_previous_services.groupby("DESCRICAO DO SERVICO").size().reset_index(name="RETRABALHOS")
    )

    # Junta eles
    df_merge = pd.merge(df_os_agg, df_previous_services_agg, on="DESCRICAO DO SERVICO", how="left")
    df_merge = pd.merge(df_merge, df_fixes_agg, on="DESCRICAO DO SERVICO", how="left")

    # Calcula as percentagens
    df_merge["PERC_RETRABALHO"] = 100 * (df_merge["RETRABALHOS"] / df_merge["TOTAL_DE_OS"])
    df_merge["PERC_CORRECOES"] = 100 * (df_merge["CORRECOES"] / df_merge["TOTAL_DE_OS"])

    # Ordena por percentagem
    df_merge = df_merge.sort_values(by="PERC_RETRABALHO", ascending=True)

    return df_merge, df_below_threshold, df_previous_services, df_fixes


@callback(
    Output("store-dados-os", "data"),
    [
        Input("input-lista-os", "value"),
        Input("input-intervalo-datas", "value"),
        Input("input-dias", "value"),
    ],
)
def computa_retrabalho(lista_os, datas, min_dias):
    dados_vazios = {
        "df_estatistica": pd.DataFrame().to_dict("records"),
        "df_below_threshold": pd.DataFrame().to_dict("records"),
        "df_previous_services": pd.DataFrame().to_dict("records"),
        "df_fixes": pd.DataFrame().to_dict("records"),
        "vazio": True,
    }

    if (lista_os is None or not lista_os) or (datas is None or not datas or None in datas):
        return dados_vazios

    #####
    # Obtém os dados de retrabalho
    #####
    df_os = obtem_dados_os(lista_os)

    # Filtrar os dados
    inicio = pd.to_datetime(datas[0])
    fim = pd.to_datetime(datas[1])

    # Filtrar os dados
    df_filtro = df_os[(df_os["DATA_INICIO_SERVICO_DT"] >= inicio) & (df_os["DATA_FECHAMENTO_SERVICO_DT"] <= fim)]

    # Verifica se há dados, caso negativo retorna vazio
    if df_filtro.empty:
        return dados_vazios

    # Obtem os dados de retrabalho
    df_estatistica, df_below_threshold, df_previous_services, df_fixes = obtem_estatistica_retrabalho(
        df_filtro, min_dias
    )

    return {
        "df_estatistica": df_estatistica.to_dict("records"),
        "df_below_threshold": df_below_threshold.to_dict("records"),
        "df_previous_services": df_previous_services.to_dict("records"),
        "df_fixes": df_fixes.to_dict("records"),
        "df_os_filtradas": df_filtro.to_dict("records"),
        "vazio": False,
    }


@callback(Output("graph-retrabalho-correcoes", "figure"), Input("store-dados-os", "data"))
def plota_grafico_pizza_retrabalho(data):
    if data["vazio"]:
        return go.Figure()

    #####
    # Obtém os dados de retrabalho
    #####
    df_estatistica = pd.DataFrame(data["df_estatistica"])
    df_below_threshold = pd.DataFrame(data["df_below_threshold"])
    df_previous_services = pd.DataFrame(data["df_previous_services"])
    df_fixes = pd.DataFrame(data["df_fixes"])

    # Prepara os dados para o gráfico
    labels = ["Retrabalhos", "Correções"]
    values = [df_estatistica["RETRABALHOS"].sum(), df_estatistica["CORRECOES"].sum()]
    df_pie = pd.DataFrame({"CATEGORIA": labels, "QUANTIDADE": values})

    # Gera o gráfico
    fig = px.pie(
        df_pie,
        values="QUANTIDADE",
        names="CATEGORIA",
        color_discrete_sequence=tema.PALETA_CORES_QUALITATIVA,
    )
    # Atualiza as fontes
    fig.update_layout(font_family=tema.FONTE_GRAFICOS, font_size=tema.FONTE_TAMANHO)

    # Arruma legenda e texto
    fig.update_traces(textinfo="value+percent", sort=False)
    fig.update_layout(
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="bottom",  # Anchor the legend to the bottom of the chart
            y=-0.1,  # Position the legend slightly below the chart
            xanchor="center",  # Center the legend horizontally
            x=0.5,  # Center position
        )
    )

    # Retorna o gráfico
    return fig


@callback(Output("graph-retrabalho-cumulativo", "figure"), Input("store-dados-os", "data"))
def plota_grafico_cumulativo_retrabalho(data):
    if data["vazio"]:
        return go.Figure()

    #####
    # Obtém os dados de retrabalho
    #####
    df_estatistica = pd.DataFrame(data["df_estatistica"])
    df_below_threshold = pd.DataFrame(data["df_below_threshold"])
    df_previous_services = pd.DataFrame(data["df_previous_services"])
    df_fixes = pd.DataFrame(data["df_fixes"])

    # Ordenando os dados e criando a coluna cumulativa em termos percentuais
    df_fixes_sorted = df_fixes.sort_values(by="DIAS_ATE_OS_CORRIGIR").copy()
    df_fixes_sorted["cumulative_percentage"] = (
        df_fixes_sorted["DIAS_ATE_OS_CORRIGIR"].expanding().count() / len(df_fixes_sorted) * 100
    )

    # Criando o gráfico cumulativo com o eixo y em termos percentuais
    fig = px.line(
        df_fixes_sorted,
        x="DIAS_ATE_OS_CORRIGIR",
        y="cumulative_percentage",
        labels={"DIAS_ATE_OS_CORRIGIR": "Dias", "cumulative_percentage": "Correções Cumulativas (%)"},
        color_discrete_sequence=tema.PALETA_CORES_QUALITATIVA,
    )

    fig.update_traces(
        mode="markers+lines",
    )

    # Adiciona o Topo
    df_top = df_fixes_sorted.groupby("DIAS_ATE_OS_CORRIGIR", as_index=False).agg(
        cumulative_percentage=("cumulative_percentage", "max"), count=("DIAS_ATE_OS_CORRIGIR", "count")
    )
    df_top["label"] = df_top.apply(lambda row: f"{row['cumulative_percentage']:.0f}% <br>({row['count']})", axis=1)

    fig.add_scatter(
        x=df_top["DIAS_ATE_OS_CORRIGIR"],
        y=df_top["cumulative_percentage"],
        mode="text",
        text=df_top["label"],
        textposition="middle right",
        showlegend=False,
        marker=dict(color=tema.PALETA_CORES_QUALITATIVA[0]),
    )

    fig.update_layout(
        xaxis=dict(range=[-1, df_fixes_sorted["DIAS_ATE_OS_CORRIGIR"].max() + 3]),
    )

    # Atualiza as fontes
    fig.update_layout(font_family=tema.FONTE_GRAFICOS, font_size=tema.FONTE_TAMANHO)

    # Retorna o gráfico
    return fig


@callback(Output("graph-retrabalho-por-modelo", "figure"), Input("store-dados-os", "data"))
def plota_grafico_cumulativo_retrabalho(data):
    if data["vazio"]:
        return go.Figure()

    #####
    # Obtém os dados de retrabalho
    #####
    df_estatistica = pd.DataFrame(data["df_estatistica"])
    df_below_threshold = pd.DataFrame(data["df_below_threshold"])
    df_previous_services = pd.DataFrame(data["df_previous_services"])
    df_fixes = pd.DataFrame(data["df_fixes"])
    df_os_filtradas = pd.DataFrame(data["df_os_filtradas"])

    # Agrupa por modelo
    df_fixes_agg_por_modelo = (
        df_fixes.groupby(["DESCRICAO DO SERVICO", "DESCRICAO DO MODELO"]).size().reset_index(name="CORRECOES")
    )
    df_previous_agg_por_modelo = (
        df_previous_services.groupby(["DESCRICAO DO SERVICO", "DESCRICAO DO MODELO"])
        .size()
        .reset_index(name="RETRABALHOS")
    )
    df_os_agg_por_modelo = (
        df_os_filtradas.groupby(["DESCRICAO DO SERVICO", "DESCRICAO DO MODELO"]).size().reset_index(name="TOTAL_DE_OS")
    )

    # Faz o merge
    df_merge_modelo = pd.merge(
        df_os_agg_por_modelo,
        df_previous_agg_por_modelo,
        on=["DESCRICAO DO SERVICO", "DESCRICAO DO MODELO"],
        how="outer",
    )
    df_merge_modelo = pd.merge(
        df_merge_modelo, df_fixes_agg_por_modelo, on=["DESCRICAO DO SERVICO", "DESCRICAO DO MODELO"], how="outer"
    )
    df_merge_modelo = df_merge_modelo.fillna(0)
    df_merge_modelo = df_merge_modelo.astype({"CORRECOES": int, "RETRABALHOS": int, "TOTAL_DE_OS": int})

    # Computa as percentagens
    df_merge_modelo["PERC_RETRABALHO"] = 100 * (df_merge_modelo["RETRABALHOS"] / df_merge_modelo["TOTAL_DE_OS"])
    df_merge_modelo["PERC_CORRECOES"] = 100 * (df_merge_modelo["CORRECOES"] / df_merge_modelo["TOTAL_DE_OS"])

    # Gera o gráfico
    bar_chart = px.bar(
        df_merge_modelo,
        x="DESCRICAO DO MODELO",
        y=["PERC_RETRABALHO", "PERC_CORRECOES"],
        barmode="stack",
        color_discrete_sequence=tema.PALETA_CORES_QUALITATIVA,
        labels={
            "value": "Percentagem",
            "DESCRICAO DO SERVICO": "Ordem de Serviço",
            "variable": "Itens",
        },
    )

    # Atualizando os valores de rótulo para PERC_RETRABALHO (percentual e valor absoluto de retrabalhos)
    bar_chart.update_traces(
        text=[
            f"{retrabalho} ({perc_retrab:.2f}%)"
            for retrabalho, perc_retrab in zip(df_merge_modelo["RETRABALHOS"], df_merge_modelo["PERC_RETRABALHO"])
        ],
        selector=dict(name="PERC_RETRABALHO"),
    )

    # Atualizando os valores de rótulo para PERC_CORRECOES (percentual e valor absoluto de correções)
    bar_chart.update_traces(
        text=[
            f"{correcoes} ({perc_correcoes:.2f}%)"
            for correcoes, perc_correcoes in zip(df_merge_modelo["CORRECOES"], df_merge_modelo["PERC_CORRECOES"])
        ],
        selector=dict(name="PERC_CORRECOES"),
    )

    # Exibir os rótulos nas barras
    bar_chart.update_traces(texttemplate="%{text}")

    # Atualiza as fontes
    bar_chart.update_layout(font_family=tema.FONTE_GRAFICOS, font_size=tema.FONTE_TAMANHO)

    # Retorna o gráfico
    return bar_chart


@callback(
    [
        Output("indicador-total-os", "children"),
        Output("indicador-porcentagem-retrabalho", "children"),
        Output("indicador-num-medio-dias-correcao", "children"),
        Output("indicador-num-medio-de-os-ate-correcao", "children"),
    ],
    Input("store-dados-os", "data"),
)
def atualiza_indicadores(data):
    if data["vazio"]:
        return ["", "", "", ""]

    #####
    # Obtém os dados de retrabalho
    #####
    df_estatistica = pd.DataFrame(data["df_estatistica"])
    df_below_threshold = pd.DataFrame(data["df_below_threshold"])
    df_previous_services = pd.DataFrame(data["df_previous_services"])
    df_fixes = pd.DataFrame(data["df_fixes"])

    # Valores
    total_de_os = int(df_estatistica["TOTAL_DE_OS"].sum())
    total_de_retrabalhos = round(float(df_estatistica["PERC_RETRABALHO"].mean()), 1)
    dias_ate_corrigir = round(float(df_fixes["DIAS_ATE_OS_CORRIGIR"].mean()), 2)
    num_os_ate_corrigir = round(float(df_fixes["NUM_OS_ATE_OS_CORRIGIR"].mean()), 2)

    return [f"{total_de_os} OS", f"{total_de_retrabalhos}%", f"{dias_ate_corrigir}", f"{num_os_ate_corrigir} OS"]


@callback(
    Output("tabela-top-10-os-problematicas", "rowData"),
    Input("store-dados-os", "data"),
)
def update_tabela_os_problematicas(data):
    if data["vazio"]:
        return []

    #####
    # Obtém os dados de retrabalho
    #####
    df_estatistica = pd.DataFrame(data["df_estatistica"])
    df_below_threshold = pd.DataFrame(data["df_below_threshold"])
    df_previous_services = pd.DataFrame(data["df_previous_services"])
    df_fixes = pd.DataFrame(data["df_fixes"])

    df_tabela = df_fixes.sort_values(by=["DIAS_ATE_OS_CORRIGIR"], ascending=False).copy()
    df_tabela["DIA"] = pd.to_datetime(df_tabela["DATA_INICIO_SERVICO_DT"]).dt.strftime("%d/%m/%Y")

    # Retorna tabela
    return df_tabela.to_dict("records")


@callback(
    Output("tabela-top-10-veiculos", "rowData"),
    Input("store-dados-os", "data"),
)
def update_tabela_veiculos_problematicos(data):
    if data["vazio"]:
        return []

    #####
    # Obtém os dados de retrabalho
    #####
    df_estatistica = pd.DataFrame(data["df_estatistica"])
    df_below_threshold = pd.DataFrame(data["df_below_threshold"])
    df_previous_services = pd.DataFrame(data["df_previous_services"])
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
    df_estatistica = pd.DataFrame(data["df_estatistica"])
    df_below_threshold = pd.DataFrame(data["df_below_threshold"])
    df_previous_services = pd.DataFrame(data["df_previous_services"])
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
    df_estatistica = pd.DataFrame(data["df_estatistica"])
    df_below_threshold = pd.DataFrame(data["df_below_threshold"])
    df_previous_services = pd.DataFrame(data["df_previous_services"])
    df_fixes = pd.DataFrame(data["df_fixes"])
    df_os_filtradas = pd.DataFrame(data["df_os_filtradas"])

    # Filtra as OS do veículo
    df_previous_services_vec = df_previous_services[df_previous_services["CODIGO DO VEICULO"] == vec_detalhar].copy()
    df_previous_services_vec["CLASSIFICACAO"] = "Retrabalho"
    df_previous_services_vec["CLASSIFICACAO_EMOJI"] = "❌"

    df_fixes_vec = df_fixes[df_fixes["CODIGO DO VEICULO"] == vec_detalhar].copy()
    df_fixes_vec["CLASSIFICACAO"] = "Correção"
    df_fixes_vec["CLASSIFICACAO_EMOJI"] = "✅"

    # Junta os dados
    df_detalhar = pd.concat([df_previous_services_vec, df_fixes_vec])
    df_detalhar = df_detalhar.sort_values(by=['CODIGO DO VEICULO', 'DESCRICAO DO SERVICO', 'DATA_INICIO_SERVICO_DT'])
    
    # Formata datas
    df_detalhar["DIA_INICIO"] = pd.to_datetime(df_detalhar["DATA INICIO SERVICO"]).dt.strftime("%d/%m/%Y")
    df_detalhar["DIA_TERMINO"] = pd.to_datetime(df_detalhar["DATA DE FECHAMENTO DO SERVICO"]).dt.strftime("%d/%m/%Y")

    # Computa DIFF
    df_detalhar["DIFF_DAYS"] = pd.to_datetime(df_detalhar["DATA INICIO SERVICO"]).diff().dt.days
    df_detalhar["DIFF_DAYS"] = df_detalhar["DIFF_DAYS"].fillna(0)
    df_detalhar["DIFF_DAYS"] = df_detalhar["DIFF_DAYS"].astype(int)

    # Seleciona os motoristas
    df_motoristas = pd.read_sql_query("""SELECT * FROM motoristas""", con_banco_assets)

    # Mescla
    df_merge = df_detalhar.merge(df_motoristas, left_on="COLABORADOR QUE EXECUTOU O SER", right_on="ID Colaborador")

    return df_merge.to_dict("records")
