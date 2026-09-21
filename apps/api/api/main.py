from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routers import auth, chat, documents, projects, search, users, zones

settings = get_settings()

app = FastAPI(title="NBCC Document Archive API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(zones.router)
app.include_router(projects.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(chat.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
