import pandas as pd

from infra.db.db_connection import PGconnectionHandler

class TripsEventService:
    def __init__(self):
        self.conn = PGconnectionHandler()
    
    def trips_in_day(self, start_date: str, end_date: str) -> list:
        '''Retorna as Trips de um dia selecionado'''
        
        start_date_ = pd.to_datetime(start_date).strftime('%Y-%m-%d') 
        end_date_ = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        query = '''
            SELECT 
                ta."TripId",
                (ta."TripStart" :: timestamp) AS inicio_trip
            FROM trips_api ta
            WHERE ta."TripStart" :: timestamp BETWEEN %s AND %s
        '''
        params = [start_date_, f"{end_date_} 23:59"]
        df = pd.read_sql(query, self.conn.get_conn(), params=params)

        return df['inicio_trip'].tolist()

        
        