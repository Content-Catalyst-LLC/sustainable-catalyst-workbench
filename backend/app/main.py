import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.release import APP_VERSION

app = FastAPI(title="Sustainable Catalyst Workbench", version=APP_VERSION)
# Static release identity marker: version="6.6.0"
version=APP_VERSION

def _allowed_origins():
    configured = [item.strip() for item in os.getenv("SCWB_ALLOWED_ORIGINS", "").split(",") if item.strip()]
    return configured or [
        "https://sustainablecatalyst.com",
        "https://www.sustainablecatalyst.com",
        "http://localhost",
        "http://127.0.0.1",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "X-Request-ID", "X-SC-Service-Token", "X-SC-Gateway-Service", "X-SC-Core-Version"],
)

@app.middleware("http")
async def workbench_request_identity(request: Request, call_next):
    """Preserve Core request identity without exposing credentials."""
    request_id = request.headers.get("x-request-id", "").strip()
    response = await call_next(request)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    response.headers["X-SC-Workbench-Version"] = APP_VERSION
    return response

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


# Workbench v3.1.0 persistent project workspace routes.
from app.v310 import router as v310_router
app.include_router(v310_router)


# Workbench v3.2.0 Knowledge Library and Article Integration routes.
from app.v320 import router as v320_router
app.include_router(v320_router)


# Workbench v3.3.0 Platform Handoffs and Shared Evidence routes.
from app.v330 import router as v330_router
app.include_router(v330_router)


# Workbench v3.4.0 Collaboration, Review, and Technical Sign-Off routes.
from app.v340 import router as v340_router
app.include_router(v340_router)


# Workbench v3.5.0 Advanced Device and Instrument Orchestration routes.
from app.v350 import router as v350_router
app.include_router(v350_router)


# Workbench v3.6.0 Computational Intelligence and Predictive Analytics routes.
from app.v360 import router as v360_router
app.include_router(v360_router)


# Workbench v3.7.0 Domain Laboratory Integration routes.
from app.v370 import router as v370_router
app.include_router(v370_router)


# Workbench v3.8.0 Offline and Installable Workbench routes.
from app.v380 import router as v380_router
app.include_router(v380_router)


# Workbench v3.9.0 Production Evaluation and Public Release Hardening routes.
from app.v390 import router as v390_router
app.include_router(v390_router)


# Workbench v4.0.0 Connected Scientific and Engineering Workbench routes.
from app.v400 import router as v400_router
app.include_router(v400_router)


# Workbench v4.0.1 Connected Environment Activation and Integration Reliability routes.
from app.v401 import router as v401_router
app.include_router(v401_router)


# Workbench v4.0.2 Project Graph, Synchronization, and Recovery Hardening routes.
from app.v402 import router as v402_router
app.include_router(v402_router)


# Workbench v4.1.0 Hosted Collaborative Workspace and Authenticated Team Projects routes.
from app.v410 import router as v410_router
app.include_router(v410_router)


# Workbench v4.2.0 Workflow Templates and Guided Scientific/Engineering Project Creation routes.
from app.v420 import router as v420_router
app.include_router(v420_router)


# Workbench v4.3.0 Live Data Connectors and Reproducible Dataset Pipelines routes.
from app.v430 import router as v430_router
app.include_router(v430_router)


# Workbench v4.4.0 Automated Evaluation, Benchmarking, and Comparison Laboratory routes.
from app.v440 import router as v440_router
app.include_router(v440_router)


# Workbench v4.5.0 Extension SDK, Plugin Registry, and Third-Party Module Framework routes.
from app.v450 import router as v450_router
app.include_router(v450_router)


# Workbench v5.0.0 Sustainable Catalyst Integrated Research and Engineering Platform routes.
from app.v500 import router as v500_router
app.include_router(v500_router)


# Workbench v5.1.0 Universal Mathematics & CAS Engine Foundation routes.
from app.v510 import router as v510_router
app.include_router(v510_router)


# Workbench v5.2.0 Interactive Graph Mathematics routes.
from app.v520 import router as v520_router
app.include_router(v520_router)


# Workbench v5.3.0 Computational Blackboard, Creative Mathematics & Physical Prototyping routes.
from app.v530 import router as v530_router
app.include_router(v530_router)


# Workbench v5.4.0 Advanced Graph Mathematics II routes.
from app.v540 import router as v540_router
app.include_router(v540_router)


# Workbench v5.5.0 Dynamic Geometry & Interactive Mathematics routes.
from app.v550 import router as v550_router
app.include_router(v550_router)

# Workbench v5.6.0 Numerical Methods & Scientific Computing routes.
from app.v560 import router as v560_router
app.include_router(v560_router)


# Workbench v5.7.0 Signals, Systems & Control Mathematics routes.
from app.v570 import router as v570_router
app.include_router(v570_router)


# Workbench v5.8.0 Electronics & Embedded Systems Studio routes.
from app.v580 import router as v580_router
app.include_router(v580_router)


# Workbench v5.9.0 FPGA, PYNQ & Digital Logic Workbench routes.
from app.v590 import router as v590_router
app.include_router(v590_router)


# Workbench v6.0.0 Unified Computational Workbench routes.
from app.v600 import router as v600_router
app.include_router(v600_router)


# Workbench v6.0.1 Unified Experience, Runtime Identity & Interface Hardening routes.
from app.v601 import router as v601_router
app.include_router(v601_router)


# Energy Systems Intelligence v1.2.0 target-side runtime consumer.
from .energy_runtime_consumer import router as energy_runtime_consumer_router
app.include_router(energy_runtime_consumer_router)


# Workbench v6.2.0 — Energy Workbench Runtime routes.
from app.v620 import router as v620_router
app.include_router(v620_router)

# Energy Systems Intelligence v1.3.0 explicit-input execution runtime.
from .energy_workbench_runtime import router as energy_workbench_runtime_router
app.include_router(energy_workbench_runtime_router)


# Workbench v6.3.0 — Grid, Storage & Reliability Analysis routes.
from app.v630 import router as v630_router
app.include_router(v630_router)


# Workbench v6.4.0 — Platform Core Connectivity Foundation routes.
from app.v640 import router as v640_router
app.include_router(v640_router)


# Workbench v6.5.0 — Unified Runtime Contract Adapter routes.
from app.v650 import router as v650_router
app.include_router(v650_router)


# Workbench v6.6.0 — Unified Research Project & Session Bridge routes.
from app.v660 import router as v660_router
app.include_router(v660_router)
