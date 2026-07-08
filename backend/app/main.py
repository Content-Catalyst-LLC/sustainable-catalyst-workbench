from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ai, research, tools
from app.core.settings import settings

app = FastAPI(
    title="Sustainable Catalyst Workbench API",
    version="0.1.0",
    description="Site-scoped analytical backend for Sustainable Catalyst Workbench.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tools.router)
app.include_router(ai.router)
app.include_router(research.router)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "sustainable-catalyst-workbench-api", "version": "0.1.0"}
