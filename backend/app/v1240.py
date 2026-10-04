"""Workbench v12.4.0 — Standalone Mathematical View Renderer.

Backend contract for the standalone browser renderer. Mathematical sampling and
view-spec generation remain authoritative in v11.16. v12.4 publishes renderer
capabilities and a session-authorized graphing bridge without duplicating math.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Header
from pydantic import BaseModel
from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v11160 import GraphingRequest, execute_graphing
from .v1210 import require_session
from .v510 import content_hash

VERSION=APP_VERSION
STATUS_SCHEMA="sc-workbench-standalone-mathematical-renderer-status/1.0"
CONFIG_SCHEMA="sc-workbench-standalone-mathematical-renderer-config/1.0"
router=APIRouter(tags=["workbench-v1240-standalone-mathematical-view-renderer"])

class RenderRequest(BaseModel):
    graphing: GraphingRequest

def _hash(x:Any)->str:
    return content_hash(x)

def renderer_config()->Dict[str,Any]:
    body={
      "schema":CONFIG_SCHEMA,
      "version":VERSION,
      "renderer":"standalone-svg-view-renderer/1.0",
      "wordpressRequired":False,
      "viewSpecSchema":"sc-workbench-mathematical-view-spec/1.0",
      "supportedKinds":[
        "cartesian-function","derivative","accumulated-integral",
        "parametric","polar","implicit-field","linked-table"
      ],
      "interactions":{
        "crosshair":True,"zoom":True,"pan":True,
        "linkedSelection":True,"linkedDomain":True
      },
      "rendering":{
        "vectorGraphics":"svg",
        "implicitField":"canvas-or-svg-cell-map",
        "linkedTable":"html-table",
        "browserSideMathExecution":False,
        "backendViewSpecAuthority":True
      }
    }
    body["configHash"]=_hash(body)
    return body

def status()->Dict[str,Any]:
    c=renderer_config()
    return {
      "ok":True,"schema":STATUS_SCHEMA,"version":VERSION,
      "release":"Standalone Mathematical View Renderer",
      "product":PRODUCT_KEY,"runtime":RUNTIME_KIND,
      "wordpressRequired":False,
      "viewSpecAuthority":"v11.16 backend",
      "rendererAuthority":"standalone-app",
      "configHash":c["configHash"],
      "capabilities":{
        "standaloneSvgRenderer":True,
        "cartesianSeries":True,
        "parametricSeries":True,
        "polarSeries":True,
        "implicitFields":True,
        "rootMarkers":True,
        "criticalPointMarkers":True,
        "derivativeViews":True,
        "integralViews":True,
        "linkedTables":True,
        "crosshairInteraction":True,
        "linkedViewContract":True,
        "wordpressRendererNotRequired":True
      }
    }

@router.get("/v1240/status")
def status_route():
    return status()

@router.get("/standalone/v1/renderer/config")
def config_route(authorization:Optional[str]=Header(default=None)):
    s=require_session(authorization)
    return {"ok":True,"version":VERSION,"sessionId":s["sessionId"],"renderer":renderer_config()}

@router.post("/standalone/v1/renderer/view-spec")
def view_spec_route(req:RenderRequest, authorization:Optional[str]=Header(default=None)):
    s=require_session(authorization)
    result=execute_graphing(req.graphing)
    return {
      "ok":True,"version":VERSION,"sessionId":s["sessionId"],
      "renderer":renderer_config()["renderer"],
      "viewSpec":result,
      "wordpressRequired":False
    }
