# Graficos de Evolução do Retrabalho por Garagem e Seção
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Peças trocadas por mês", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-pecas-trocadas-por-mes"),
        dmc.Space(h=40),



@callback(
    Output("graph-pecas-trocadas-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-veiculo-selecionado", "value"),
    ],
)

def plota_grafico_pecas_trocadas_por_mes(datas, veiculo_id):
    # Valida input
    if not datas or not veiculo_id:
        return go.Figure()

    # Datas
    data_inicio_str = datas[0]
    data_fim_str = datas[1]

    # Query para buscar peças trocadas por mês
    query = f"""
    SELECT 
        to_char("DATA_TROCA", 'YYYY-MM') AS year_month,
        SUM("QUANTIDADE") AS total_pecas
    FROM 
        pecas_gerais
    WHERE 
        "ID_VEICULO" = {veiculo_id}
        AND "DATA_TROCA" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
    GROUP BY 
        year_month
    ORDER BY 
        year_month;
    """

    # Executa a query
    df = pd.read_sql(query, pgEngine)

    # Converte a coluna para datetime para ordenar corretamente
    df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

    # Gera o gráfico de barras
    fig = px.bar(
        df,
        x="year_month_dt",
        y="total_pecas",
        labels={"year_month_dt": "Mês", "total_pecas": "Quantidade de Peças"},
        title="Quantidade de Peças Trocadas por Mês",
    )

    # Personaliza o layout
    fig.update_layout(
        xaxis_title="Mês",
        yaxis_title="Quantidade de Peças",
        margin=dict(t=50, b=50, l=50, r=50),
    )

    return fig