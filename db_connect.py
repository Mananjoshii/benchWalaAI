import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env

def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT", 3306)
    )
    return connection