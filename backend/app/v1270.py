"""Workbench v12.7.0 — WordPress Embed & Deep-Link Compatibility.

Defines a thin compatibility boundary for launching the standalone Workbench
from WordPress or other public-site surfaces. Launch descriptors are signed for
integrity but are not authentication credentials. The standalone app still
creates/validates its own v12.1 session and enforces resource ownership.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1210 import require_session
from .v510 import content_hash

VERSION=APP_VERSION
STATUS_SCHEMA="sc-workbench-wordpress-embed-deep-link-status/1.0"
LAUNCH_SCHEMA="sc-workbench-launch-descriptor/1.0"
EMBED_SCHEMA="sc-workbench-embed-config/1.0"

router=APIRouter(tags=["workbench-v1270-wordpress-embed-deep-link-compatibility"])

_ALLOWED_ROUTES={"/calculator","/workspace","/graphs","/history","/packages","/settings"}
_ALLOWED_TARGETS={"none","project","calculation","package"}
_DEFAULT_APP_URL="https://workbench.sustainablecatalyst.com"


class LaunchRequest(BaseModel):
    route:str=Field(default="/calculator",max_length=100)
    targetType:Literal["none","project","calculation","package"]="none"
    targetId:Optional[str]=Field(default=None,max_length=160)
    source:Literal["wordpress","direct","publication","library","other"]="wordpress"
    embed:bool=False
    ttlSeconds:int=Field(default=900,ge=60,le=86400)
    context:Dict[str,Any]=Field(default_factory=dict)


class ValidateLaunchRequest(BaseModel):
    token:str=Field(min_length=20,max_length=20000)


def _hash(x:Any)->str:
    return content_hash(x)


def _secret()->bytes:
    raw=os.getenv("SCWB_DEEP_LINK_SECRET","").strip() or os.getenv("SCWB_SESSION_SECRET","").strip()
    if raw:
        return raw.encode("utf-8")
    # Stable development fallback only within process; callers can inspect config.
    return _FALLBACK_SECRET


_FALLBACK_SECRET=os.urandom(32)


def _secret_state():
    deep=bool(os.getenv("SCWB_DEEP_LINK_SECRET","").strip())
    session=bool(os.getenv("SCWB_SESSION_SECRET","").strip())
    return {
      "source":"SCWB_DEEP_LINK_SECRET" if deep else ("SCWB_SESSION_SECRET" if session else "process-ephemeral"),
      "durableAcrossRestart":deep or session
    }


def _b64e(raw:bytes)->str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(text:str)->bytes:
    return base64.urlsafe_b64decode(text+"="*((4-len(text)%4)%4))


def _canonical(payload:Dict[str,Any])->bytes:
    return json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()


def _sign(payload:Dict[str,Any])->str:
    body=_b64e(_canonical(payload))
    sig=hmac.new(_secret(),body.encode(),hashlib.sha256).digest()
    return f"scwbl1.{body}.{_b64e(sig)}"


def _decode(token:str)->Dict[str,Any]:
    try:
        prefix,body,sig=token.split(".",2)
    except ValueError as exc:
        raise HTTPException(status_code=400,detail="Malformed Workbench launch token") from exc
    if prefix!="scwbl1":
        raise HTTPException(status_code=400,detail="Unsupported Workbench launch token")
    expected=hmac.new(_secret(),body.encode(),hashlib.sha256).digest()
    try:
        observed=_b64d(sig)
    except Exception as exc:
        raise HTTPException(status_code=400,detail="Malformed Workbench launch signature") from exc
    if not hmac.compare_digest(expected,observed):
        raise HTTPException(status_code=400,detail="Invalid Workbench launch signature")
    try:
        payload=json.loads(_b64d(body).decode())
    except Exception as exc:
        raise HTTPException(status_code=400,detail="Malformed Workbench launch payload") from exc
    if payload.get("schema")!=LAUNCH_SCHEMA:
        raise HTTPException(status_code=400,detail="Unsupported Workbench launch schema")
    if int(payload.get("expiresAt",0))<=int(time.time()):
        raise HTTPException(status_code=400,detail="Workbench launch token expired")
    return payload


def app_url()->str:
    return os.getenv("SCWB_STANDALONE_APP_URL","").strip().rstrip("/") or _DEFAULT_APP_URL


def embed_config()->Dict[str,Any]:
    ss=_secret_state()
    body={
      "schema":EMBED_SCHEMA,"version":VERSION,
      "standaloneAppUrl":app_url(),
      "wordpressRequired":False,
      "wordpressRole":"embed-and-launch-compatibility-only",
      "launchTokenFormat":"scwbl1",
      "launchSigning":ss,
      "embed":{
        "allowed":True,
        "sandboxRecommendation":"allow-scripts allow-same-origin allow-forms allow-popups",
        "defaultHeight":760,
        "responsive":True
      },
      "deepLinks":{
        "allowedRoutes":sorted(_ALLOWED_ROUTES),
        "targetTypes":sorted(_ALLOWED_TARGETS),
        "authenticationEmbedded":False,
        "ownershipChecksDeferredToStandaloneSession":True
      }
    }
    body["configHash"]=_hash(body)
    return body


def create_launch(req:LaunchRequest)->Dict[str,Any]:
    if req.route not in _ALLOWED_ROUTES:
        raise HTTPException(status_code=422,detail="Unsupported standalone route")
    if req.targetType!="none" and not req.targetId:
        raise HTTPException(status_code=422,detail="targetId required for selected targetType")
    now=int(time.time())
    payload={
      "schema":LAUNCH_SCHEMA,"version":VERSION,
      "route":req.route,"targetType":req.targetType,"targetId":req.targetId,
      "source":req.source,"embed":req.embed,"context":req.context,
      "issuedAt":now,"expiresAt":now+req.ttlSeconds,
      "authenticationEmbedded":False
    }
    payload["descriptorHash"]=_hash(payload)
    token=_sign(payload)
    url=f"{app_url()}{req.route}?{urlencode({'launch':token})}"
    return {
      "ok":True,"version":VERSION,"launchDescriptor":payload,
      "launchToken":token,"launchUrl":url,
      "wordpressRequired":False
    }


def validate_launch(token:str)->Dict[str,Any]:
    payload=_decode(token)
    expected_hash=payload.get("descriptorHash")
    material={k:v for k,v in payload.items() if k!="descriptorHash"}
    valid_hash=expected_hash==_hash(material)
    if not valid_hash:
        raise HTTPException(status_code=400,detail="Workbench launch descriptor hash mismatch")
    return {
      "ok":True,"version":VERSION,"valid":True,
      "launchDescriptor":payload,
      "authenticationEmbedded":False,
      "wordpressRequired":False
    }


def status():
    c=embed_config()
    return {
      "ok":True,"schema":STATUS_SCHEMA,"version":VERSION,
      "release":"WordPress Embed & Deep-Link Compatibility",
      "product":PRODUCT_KEY,"runtime":RUNTIME_KIND,
      "wordpressRequired":False,"standaloneAppUrl":app_url(),
      "configHash":c["configHash"],
      "capabilities":{
        "wordpressEmbedCompatibility":True,
        "signedDeepLinks":True,
        "tamperDetection":True,
        "expiringLaunchDescriptors":True,
        "projectTargets":True,
        "calculationTargets":True,
        "packageTargets":True,
        "standaloneRouteTargets":True,
        "authenticationNotEmbeddedInLaunch":True,
        "standaloneOwnershipEnforcementPreserved":True,
        "wordpressStateAuthority":False
      }
    }


@router.get("/v1270/status")
def status_route(): return status()

@router.get("/standalone/v1/launch/config")
def config_route():
    return {"ok":True,"version":VERSION,"launch":embed_config()}

@router.post("/standalone/v1/launch")
def launch_route(req:LaunchRequest):
    return create_launch(req)

@router.post("/standalone/v1/launch/validate")
def validate_route(req:ValidateLaunchRequest):
    return validate_launch(req.token)

@router.get("/standalone/v1/launch/session-check")
def session_check_route(authorization:Optional[str]=Header(default=None)):
    s=require_session(authorization)
    return {
      "ok":True,"version":VERSION,"sessionId":s["sessionId"],
      "subject":s["subject"],"wordpressRequired":False
    }
