from fastapi import FastAPI
app = FastAPI(title="Sustainable Catalyst Workbench", version="3.0.2")
version="3.0.2"

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

# Workbench v2.7.0 scientific visualization and engineering dashboard routes.
from app.v270 import router as v270_router
app.include_router(v270_router)

# Workbench v2.8.0 experiment automation and reproducible workflow routes.
from app.v280 import router as v280_router
app.include_router(v280_router)


# Workbench v2.9.0 technical documentation and product dossier routes.
from app.v290 import router as v290_router
app.include_router(v290_router)


# Workbench v3.0.0 unified prototyping workbench routes.
from app.v300 import router as v300_router
app.include_router(v300_router)


# Workbench v3.0.1 production activation and interface reliability routes.
from app.v301 import router as v301_router
app.include_router(v301_router)


# Workbench v3.0.2 project migration, storage, and recovery routes.
from app.v302 import router as v302_router
app.include_router(v302_router)
