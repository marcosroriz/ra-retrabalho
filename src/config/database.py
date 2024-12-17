import os
from dotenv import load_dotenv # type: ignore

load_dotenv()

configPG = {
    "database": os.getenv("PGDATABASE"),
    "user": os.getenv("PGUSER"),
    "host": os.getenv("PGHOST"),
    "password": os.getenv("PGPASSWORD"),
    "port": int(os.getenv("PGPORT")),
}
