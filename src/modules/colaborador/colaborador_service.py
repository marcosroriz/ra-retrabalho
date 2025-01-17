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
            print(df_mecanicos)
            return df_mecanicos
        except Exception as e:
            return pd.DataFrame()

    def get_mecanicos(self)->pd.DataFrame:
        '''Obtêm os dados de todos os mecânicos que trabalharam na RA, mesmo os desligados'''
        try:
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
            print(df_mecanicos_todos)
            return df_mecanicos_todos
        except Exception as e:
            return pd.DataFrame()

