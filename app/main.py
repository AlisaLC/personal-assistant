from fastapi import FastAPI
from datetime import datetime

from . import routes

from .services.search import build_all_user_indexes
build_all_user_indexes()


app = FastAPI()

app.include_router(routes.static_router)
app.include_router(routes.profile_router)
app.include_router(routes.auth_router)
app.include_router(routes.notes_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
