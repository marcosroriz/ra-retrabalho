import pandas as pd
import traceback
import re

from db import PostgresSingleton

class ColaboradorService:
    def __init__(self):
        pgDB = PostgresSingleton.get_instance()
        self.pgEngine = pgDB.get_engine()

    def get_info_colaboradores(self)-> pd.DataFrame:
        '''Obtem os dados dos mecânicos informados pela RA'''
        try:
            df_mecanicos = pd.read_sql(
                """
                SELECT * FROM colaboradores_frotas_os
                """,
                self.pgEngine
            )
            df_mecanicos["LABEL_COLABORADOR"] = df_mecanicos["nome_colaborador"].apply(
                lambda x: re.sub(r"(?<!^)([A-Z])", r" \1", x)
            )
            return df_mecanicos
        except Exception as e:
            return pd.DataFrame()

    def get_mecanicos(self)->pd.DataFrame:
        '''Obtêm os dados de todos os mecânicos que trabalharam na RA, mesmo os desligados'''
        try:
            df_mecanicos_todos = pd.read_sql(
                """
                SELECT DISTINCT "COLABORADOR QUE EXECUTOU O SERVICO" 
                FROM os_dados od 
                """,
                self.pgEngine,
            )
            # Converte cod_colaborador para int
            df_mecanicos_todos["cod_colaborador"] = df_mecanicos_todos["COLABORADOR QUE EXECUTOU O SERVICO"].astype(int)

            # Faz merge dos dados dos mecânicos da RA com os dados de todos os mecânicos
            df_mecanicos_todos = df_mecanicos_todos.merge(self.get_info_colaboradores(), how="left", on="cod_colaborador")

            # Adiciona o campo não informados para os colaboradores que não estão na RA
            df_mecanicos_todos["LABEL_COLABORADOR"] = df_mecanicos_todos["LABEL_COLABORADOR"].fillna("Não Informado")

            # Adiciona o campo "cod_colaborador" para o campo LABEL
            df_mecanicos_todos["LABEL_COLABORADOR"] = (
                df_mecanicos_todos["LABEL_COLABORADOR"] + " (" + df_mecanicos_todos["cod_colaborador"].astype(str) + ")"
            )

            # Ordena os colaboradores
            df_mecanicos_todos = df_mecanicos_todos.sort_values("LABEL_COLABORADOR")
            return df_mecanicos_todos
        except Exception as e:
            return pd.DataFrame()

    def obtem_dados_os_sql(self, id_colaborador: str, lista_os: list, data_inicio: str, data_fim: str, min_dias: int):
        '''Obtem dados dos colaboradores referente as Ordem de Servico executadas'''
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
        df_os_query = pd.read_sql_query(query, self.pgEngine)

        # Tratamento de datas
        df_os_query["DATA INICIO SERVICO"] = pd.to_datetime(df_os_query["DATA INICIO SERVIÇO"])
        df_os_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(df_os_query["DATA DE FECHAMENTO DO SERVICO"])

        return df_os_query

    def obtem_estatistica_retrabalho_sql(self, df_os: pd.DataFrame, min_dias: int):
        '''Obtem estatisticas e dados analisados de retrabalho'''
        df_mecanicos = self.get_mecanicos()
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

    def obtem_dados_os_mecanico(self, id_mecanico: str):
        # Query
        query = f"""
            SELECT * 
            FROM os_dados od
            WHERE od."COLABORADOR QUE EXECUTOU O SERVICO" = {id_mecanico}
        """
        df_os_mecanico_query = pd.read_sql_query(query, self.pgEngine)
        # Tratamento de datas
        df_os_mecanico_query["DATA INICIO SERVICO"] = pd.to_datetime(df_os_mecanico_query["DATA INICIO SERVIÇO"])
        df_os_mecanico_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(
            df_os_mecanico_query["DATA DE FECHAMENTO DO SERVICO"]
        )

        return df_os_mecanico_query 
    