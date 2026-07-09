from __future__ import annotations
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routers import tools, ai, models, equations, routing, symbolic, graph

settings = get_settings()
app = FastAPI(title='Sustainable Catalyst Workbench API', version='1.2.0')
app.add_middleware(CORSMiddleware, allow_origins=settings.origins or ['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

@app.middleware('http')
async def backend_key_check(request: Request, call_next):
    if settings.backend_key and request.url.path not in {'/health', '/'}:
        supplied = request.headers.get('X-SC-Workbench-Key', '')
        if supplied != settings.backend_key:
            raise HTTPException(status_code=401, detail='Invalid Workbench backend key')
    return await call_next(request)

@app.get('/')
def root():
    return {"ok": True, "name": "Sustainable Catalyst Workbench API", "version": "1.2.0"}

@app.get('/health')
def health():
    return {"ok": True, "status": "healthy", "version": "1.2.0"}

app.include_router(tools.router)
app.include_router(ai.router)
app.include_router(models.router)
app.include_router(equations.router)
app.include_router(routing.router)
app.include_router(symbolic.router)
app.include_router(graph.router)
