from fastapi import FastAPI
app = FastAPI(title="Sustainable Catalyst Workbench", version="4.4.0")
version="4.4.0"

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
