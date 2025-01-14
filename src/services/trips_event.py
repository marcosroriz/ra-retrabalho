import pandas as pd

from db import PostgresSingleton

class TripsEventService:
    def __init__(self):
        self.conn = PostgresSingleton().get_instance()
    
    def get_vehicles(self)->pd.DataFrame:
        '''Retorna veiculos do banco'''
        query = '''
        select distinct "Description" as veiculos
        from veiculos_api va
        where "Description" not like '%-%'
        '''
        df = pd.read_sql(query, self.conn.get_engine())
        return df['veiculos'].tolist()
        
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
            query += f''' WHERE va."Description" = '{vehicle}' '''
            df = pd.read_sql(query, self.conn.get_engine())
        return df
        