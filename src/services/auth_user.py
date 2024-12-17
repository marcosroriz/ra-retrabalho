from src.infra.db.db_connection import DatabaseConnection

class UserAuthService:
    def __init__(self):
        self.conn = DatabaseConnection()

    def authenticate_user(self, username: str, password: str)-> bool:
        '''verifica se o usuario está cadastrado no banco'''
        try:
            session = self.conn.get_session()

            user = session.execute('''SELECT * FROM users_ra_dash WHERE ra_username = :username''', {"username": username}).fetchone()
            
            if user and user['ra_password'] == password:
                return True
            return False
        except Exception as e:
            print('Error ou logar', e)
            return False
        finally: 
            self.conn.close_session(session)


    def register_user(self, username: str, password: str, email: str)-> bool:
        '''Regista usuario no banco de dados'''
        try:
            session = self.conn.get_session()
            existing_user = session.execute('''SELECT * FROM users_ra_dash WHERE ra_username = :username''', {"username": username}).fetchone()
            
            if existing_user:
                return False
            
            session.execute(
                '''
                INSERT INTO users_ra_dash (ra_username, ra_password, ra_email)
                VALUES (:username, :password, :email)
                ''',
                {
                    "username": username,
                    "password": password,
                    "email": email
                }
            )
            session.commit()  
            return True
        finally:
            self.db_connection.close_session(session)