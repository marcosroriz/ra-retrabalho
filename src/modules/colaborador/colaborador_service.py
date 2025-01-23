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

    def obtem_estatistica_retrabalho_sql(self, datas, min_dias, id_colaborador):
        '''Obtem estatisticas e dados analisados de retrabalho'''
        # Datas
        print(f"id_colaborador: {id_colaborador}")
        print(f"datas: {datas}")
        print(f"min_dias: {min_dias}")
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        query = f"""
        SELECT
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            "DESCRICAO DO SERVICO",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
        GROUP BY
            year_month, "DESCRICAO DO SERVICO"
        ORDER BY
            year_month;
        """
        print(query)

        # Executa query
        df = pd.read_sql(query, self.pgEngine)
        df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")
        return df
    