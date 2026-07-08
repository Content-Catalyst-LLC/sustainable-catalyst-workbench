from __future__ import annotations
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import tools, ai
from app.core.config import settings

app = FastAPI(title="Sustainable Catalyst Workbench API", version="0.4.2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def backend_key_guard(request: Request, call_next):
    if settings.backend_key:
        supplied = request.headers.get("x-sc-workbench-key", "")
        if supplied != settings.backend_key:
            raise HTTPException(status_code=401, detail="Invalid Workbench backend key")
    return await call_next(request)

@app.get("/health")
def health():
    return {"ok": True, "status": "healthy", "version": "0.4.2"}

app.include_router(tools.router)
app.include_router(ai.router)
