from dotenv import load_dotenv
import os
load_dotenv()

config_basic = {
    "TOKEN": os.getenv("API_TOKEN"),
    "API_URL": os.getenv("API_URL"),
}
