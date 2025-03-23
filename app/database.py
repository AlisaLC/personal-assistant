from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
import time
import os

DATABASE_URL = os.getenv("DATABASE_URL")
WEBUI_DATABASE_URL = os.getenv("WEBUI_DATABASE_URL")

def get_engine(database_url: str = DATABASE_URL):
    max_retries = 5
    retry_interval = 5
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url, echo=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except OperationalError as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(retry_interval)

engine = get_engine()
webui_engine = get_engine(WEBUI_DATABASE_URL)
Base = declarative_base()
