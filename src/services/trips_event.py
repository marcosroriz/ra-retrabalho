import pandas as pd

from infra.db.db_connection import PGconnectionHandler

class TripsEventService:
    def __init__(self):
        self.conn = PGconnectionHandler()
    
    def get_veiculos()->pd.DataFrame:
        '''Retorna veiculos do banco'''
        query = '''
        select distinct "Description" as veiculos
        from veiculos_api va
        where "Description" not like '%-%'
        '''
        
        
        