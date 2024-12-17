import pandas as pd

from infra.db.db_connection import DatabaseConnection

class TripsEventService:
    def __init__(self):
        self.conn = DatabaseConnection()
    
    def number_events_per_trips(self, tripid: str) -> pd.DataFrame:
        '''Retorna de uma Dataframe com a contagem dos eventos de uma determinada trip'''
        
        query = f'''
        select distinct count(*),
        tpe.asset_id,
        tea."Description" 
        from trip_possui_evento tpe
        left join tipos_eventos_api tea  on  tpe.event_type_id = tea."EventTypeId"
        where trip_id = {tripid}
        group by tpe.asset_id, tea."Description" 
        '''
        
        return pd.read_sql(query, self.conn)
    
    def trips_of_vehicle(self, frota_id: str) -> pd.DataFrame:
        '''Retorna um dataframe com os veiculos, trips e dias'''
        
        query = f'''
        select ta."TripId",
        va."Description",
        ta."TripStart":: timestamp
        from trips_api ta 
        left join veiculos_api va on ta."AssetId" = va."AssetId" 

        '''
        df = pd.read_sql(query, self.conn)
        df['Dia'] = df['TripStart'].dt.date
        return pd.read_sql(query, self.conn)