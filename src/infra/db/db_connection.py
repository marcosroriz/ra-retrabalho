from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from config import configPG

class DatabaseConnection:
    def __init__(self):
        self.__db_url = f'postgresql://{configPG['user']}:{configPG['password']}@{configPG['host']}:{configPG['port']}/{configPG['database']}'
        self.__engine = create_engine(self.__db_url)
        self.Session = sessionmaker(bind=self.__engine)

    def get_session(self):
        """ Retorna uma sessão do banco de dados """
        return self.Session()

    def close_session(self, session):
        """ Fecha a sessão """
        session.close()
