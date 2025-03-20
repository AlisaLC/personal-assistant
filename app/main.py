from fastapi import FastAPI

from .database import create_db_and_tables
from . import routes


app = FastAPI()
create_db_and_tables()

app.include_router(routes.static_router)
app.include_router(routes.profile_router)
app.include_router(routes.auth_router)
app.include_router(routes.notes_router)
