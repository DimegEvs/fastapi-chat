from dotenv import load_dotenv
import os

# dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
# if os.path.exists(dotenv_path):
load_dotenv()


DB_PORT=os.environ.get("DB_PORT")
DB_HOST=os.environ.get("DB_HOST")
DB_NAME=os.environ.get("DB_NAME")
DB_USER=os.environ.get("DB_USER")
DB_PASS=os.environ.get("DB_PASS")

URL_LOGGER = "http://fastapi-logging:8003/logger"
URL_MIDDLEWARE = "http://fastapi-logging:8003/logger_middleware"