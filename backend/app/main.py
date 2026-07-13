from __future__ import annotations
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routers import tools, ai, models, equations, routing, symbolic, graph, engineering, engineering_calculators, reports, article_embeds, code_studio

settings = get_settings()
app = FastAPI(title='Sustainable Catalyst Workbench API', version='2.4.0')
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
    return {"ok": True, "name": "Sustainable Catalyst Workbench API", "version": "2.4.0"}

@app.get('/health')
def health():
    return {"ok": True, "status": "healthy", "version": "2.4.0"}

app.include_router(tools.router)
app.include_router(ai.router)
app.include_router(models.router)
app.include_router(equations.router)
app.include_router(routing.router)
app.include_router(symbolic.router)
app.include_router(graph.router)
app.include_router(engineering.router)
app.include_router(engineering_calculators.router)
app.include_router(reports.router)
app.include_router(article_embeds.router)

app.include_router(code_studio.router)

# Workbench v2.0.0 foundation routes.
from app.v200 import router as v200_router
app.include_router(v200_router)

# Workbench v2.1.0 embedded-device routes.
from app.v210 import router as v210_router
app.include_router(v210_router)

# Workbench v2.2.0 hardware-engineering routes.
from app.v220 import router as v220_router
app.include_router(v220_router)

# Workbench v2.3.0 robotics and controls routes.
from app.v230 import router as v230_router
app.include_router(v230_router)

# Workbench v2.4.0 instrumentation and signal-analysis routes.
from app.v240 import router as v240_router
app.include_router(v240_router)

# Workbench v2.5.0 simulation, digital-twin, and systems-modeling routes.
from app.v250 import router as v250_router
app.include_router(v250_router)

# Workbench v2.6.0 multi-language engineering runtime routes.
from app.v260 import router as v260_router
app.include_router(v260_router)
