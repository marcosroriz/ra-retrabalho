import pandas as pd
import traceback

from db import PostgresSingleton

class TripsEventService:
    def __init__(self):
        pgDB = PostgresSingleton.get_instance()
        self.pgEngine = pgDB.get_engine()

    
    def get_vehicles(self)->pd.DataFrame:
        '''Retorna veiculos do banco'''
        try: 
            query = '''
                SELECT DISTINCT "Description" AS veiculos
                FROM veiculos_api
                WHERE "Description" NOT LIKE %s
            '''

            # Parametro para o LIKE, passando o '%' diretamente
            param = '%-%'

            # Execute a consulta com pandas, passando o parâmetro na tupla
            df = pd.read_sql(query, self.pgEngine, params=(param,))
            return df['veiculos'].tolist()
        except Exception as e:
            print(e)
            traceback.format_exc()
        
    def get_events(self, vehicle=None):
        '''Consulta os eventos no banco de dados com base no veículo.'''
        query = '''
        select 
        tea."Description" as evento,
        va."Description" as veiculos,
        tpe.dia_evento:: timestamp as data_evento
        from trip_possui_evento tpe 
        left join tipos_eventos_api tea on tpe.event_type_id = tea."EventTypeId"
        left join veiculos_api va on tpe.asset_id = va."AssetId" 
        '''
        if vehicle:
            query += ''' WHERE va."Description" = %s'''
            df = pd.read_sql(query, self.pgEngine, params=(vehicle,))
        return df
        