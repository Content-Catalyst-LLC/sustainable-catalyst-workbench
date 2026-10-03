"""Workbench v12.1.0 — Standalone Authentication & Session Foundation.

Provider-neutral standalone identity/session foundation. Sessions are signed
by the FastAPI backend and are independent of WordPress users, WP REST nonces,
or frontend framework state.

No password database or third-party identity provider is introduced here.
If SCWB_SESSION_SECRET is absent, a process-lifetime ephemeral secret is used
and explicitly reported as non-durable.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-standalone-auth-session-status/1.0"
AUTH_CONFIG_SCHEMA = "sc-workbench-standalone-auth-config/1.0"
SESSION_SCHEMA = "sc-workbench-standalone-session/1.0"
TOKEN_PREFIX = "scwb1"
DEFAULT_TTL_SECONDS = 3600
MAX_TTL_SECONDS = 86400

router = APIRouter(tags=["workbench-v1210-standalone-authentication-session-foundation"])

_EPHEMERAL_SECRET = secrets.token_bytes(32)


class AnonymousSessionRequest(BaseModel):
    ttlSeconds: int = Field(default=DEFAULT_TTL_SECONDS, ge=60, le=MAX_TTL_SECONDS)
    clientLabel: str = Field(default="standalone-app", max_length=200)


class SessionTokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=20000)


class RefreshSessionRequest(BaseModel):
    token: str = Field(min_length=20, max_length=20000)
    ttlSeconds: int = Field(default=DEFAULT_TTL_SECONDS, ge=60, le=MAX_TTL_SECONDS)


def _hash(payload: Any) -> str:
    return content_hash(payload)


def _secret_state() -> Dict[str, Any]:
    configured = os.getenv("SCWB_SESSION_SECRET", "")
    if configured:
        material = configured.encode("utf-8")
        source = "environment"
        durable = True
    else:
        material = _EPHEMERAL_SECRET
        source = "process-ephemeral"
        durable = False
    return {
        "material": material,
        "source": source,
        "durable": durable,
        "configured": bool(configured),
    }


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    padding = "=" * ((4 - len(text) % 4) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _canonical(payload: Dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sign_payload(payload: Dict[str, Any]) -> str:
    body = _b64e(_canonical(payload))
    secret = _secret_state()["material"]
    signature = hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest()
    return f"{TOKEN_PREFIX}.{body}.{_b64e(signature)}"


def _decode_and_verify(token: str, *, now: Optional[int] = None) -> Dict[str, Any]:
    try:
        prefix, body, sig = token.split(".", 2)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Malformed Workbench session token") from exc

    if prefix != TOKEN_PREFIX:
        raise HTTPException(status_code=401, detail="Unsupported Workbench session token")

    secret = _secret_state()["material"]
    expected = hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest()
    try:
        observed = _b64d(sig)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Malformed Workbench session signature") from exc

    if not hmac.compare_digest(expected, observed):
        raise HTTPException(status_code=401, detail="Invalid Workbench session signature")

    try:
        payload = json.loads(_b64d(body).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Malformed Workbench session payload") from exc

    current = int(time.time()) if now is None else int(now)
    if payload.get("schema") != SESSION_SCHEMA:
        raise HTTPException(status_code=401, detail="Unsupported Workbench session schema")
    if payload.get("audience") != PRODUCT_KEY:
        raise HTTPException(status_code=401, detail="Workbench session audience mismatch")
    if int(payload.get("expiresAt", 0)) <= current:
        raise HTTPException(status_code=401, detail="Workbench session expired")
    if int(payload.get("issuedAt", 0)) > current + 60:
        raise HTTPException(status_code=401, detail="Workbench session issued in the future")
    return payload


def _public_session(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema": payload["schema"],
        "sessionId": payload["sessionId"],
        "subject": payload["subject"],
        "roles": payload["roles"],
        "capabilities": payload["capabilities"],
        "authProvider": payload["authProvider"],
        "issuedAt": payload["issuedAt"],
        "expiresAt": payload["expiresAt"],
        "sessionGeneration": payload["sessionGeneration"],
        "clientLabel": payload.get("clientLabel"),
        "sessionHash": _hash({
            "sessionId": payload["sessionId"],
            "subject": payload["subject"],
            "roles": payload["roles"],
            "capabilities": payload["capabilities"],
            "issuedAt": payload["issuedAt"],
            "expiresAt": payload["expiresAt"],
            "sessionGeneration": payload["sessionGeneration"],
        }),
    }


def _new_anonymous_payload(
    ttl_seconds: int,
    client_label: str,
    *,
    session_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    generation: int = 1,
) -> Dict[str, Any]:
    now = int(time.time())
    sid = session_id or str(uuid.uuid4())
    sub = subject_id or f"anon:{uuid.uuid4()}"
    return {
        "schema": SESSION_SCHEMA,
        "version": VERSION,
        "audience": PRODUCT_KEY,
        "sessionId": sid,
        "subject": {
            "type": "anonymous",
            "id": sub,
            "authenticated": False,
        },
        "roles": ["anonymous"],
        "capabilities": [
            "calculation:execute",
            "graph:view",
            "session:inspect",
            "session:refresh",
        ],
        "authProvider": "standalone-anonymous",
        "issuedAt": now,
        "expiresAt": now + int(ttl_seconds),
        "sessionGeneration": int(generation),
        "clientLabel": client_label,
    }


def authorization_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization bearer token required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Authorization bearer token required")
    return token.strip()


def require_session(authorization: Optional[str]) -> Dict[str, Any]:
    return _decode_and_verify(authorization_token(authorization))


def auth_config() -> Dict[str, Any]:
    secret = _secret_state()
    body = {
        "schema": AUTH_CONFIG_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "application": PRODUCT_NAME,
        "wordpressRequired": False,
        "sessionTransport": "authorization-bearer",
        "tokenFormat": TOKEN_PREFIX,
        "sessionAuthority": "FastAPI",
        "sessionSigning": {
            "algorithm": "HMAC-SHA256",
            "secretSource": secret["source"],
            "durableAcrossRestart": secret["durable"],
            "productionSecretConfigured": secret["configured"],
        },
        "modes": {
            "anonymousBootstrap": {
                "enabled": True,
                "authenticated": False,
            },
            "externalIdentityProvider": {
                "enabled": False,
                "planned": True,
            },
            "wordpressUserIdentity": {
                "enabled": False,
                "required": False,
            },
        },
        "sessionPolicy": {
            "defaultTtlSeconds": DEFAULT_TTL_SECONDS,
            "maxTtlSeconds": MAX_TTL_SECONDS,
            "refreshSupported": True,
            "serverSideRevocationSupported": False,
            "revocationPlannedWithPersistentSessionStore": True,
        },
    }
    body["configHash"] = _hash(body)
    return body


def create_anonymous_session(req: AnonymousSessionRequest) -> Dict[str, Any]:
    payload = _new_anonymous_payload(req.ttlSeconds, req.clientLabel)
    token = _sign_payload(payload)
    return {
        "ok": True,
        "schema": SESSION_SCHEMA,
        "version": VERSION,
        "token": token,
        "tokenType": "Bearer",
        "session": _public_session(payload),
        "wordpressRequired": False,
    }


def verify_session(token: str) -> Dict[str, Any]:
    payload = _decode_and_verify(token)
    return {
        "ok": True,
        "schema": SESSION_SCHEMA,
        "version": VERSION,
        "valid": True,
        "session": _public_session(payload),
        "wordpressRequired": False,
    }


def refresh_session(req: RefreshSessionRequest) -> Dict[str, Any]:
    current = _decode_and_verify(req.token)
    subject = current["subject"]
    if subject.get("type") != "anonymous":
        raise HTTPException(
            status_code=400,
            detail="v12.1 refresh currently supports standalone anonymous sessions only",
        )
    payload = _new_anonymous_payload(
        req.ttlSeconds,
        current.get("clientLabel") or "standalone-app",
        session_id=current["sessionId"],
        subject_id=subject["id"],
        generation=int(current.get("sessionGeneration", 1)) + 1,
    )
    token = _sign_payload(payload)
    return {
        "ok": True,
        "schema": SESSION_SCHEMA,
        "version": VERSION,
        "token": token,
        "tokenType": "Bearer",
        "session": _public_session(payload),
        "refreshedFromGeneration": int(current.get("sessionGeneration", 1)),
        "wordpressRequired": False,
    }


def status() -> Dict[str, Any]:
    secret = _secret_state()
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Standalone Authentication & Session Foundation",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "sessionAuthority": "FastAPI",
        "sessionSecretMode": secret["source"],
        "durableSessionsAcrossRestart": secret["durable"],
        "capabilities": {
            "providerNeutralSessionBoundary": True,
            "signedBearerSessions": True,
            "anonymousBootstrapSessions": True,
            "sessionVerification": True,
            "sessionRefresh": True,
            "capabilityClaims": True,
            "sessionExpiry": True,
            "authorizationHeaderValidation": True,
            "wordpressIdentityNotRequired": True,
            "externalIdentityProviderReadyBoundary": True,
            "persistentRevocationStore": False,
        },
    }


@router.get("/v1210/status")
def status_route():
    return status()


@router.get("/standalone/v1/auth/config")
def auth_config_route():
    return {"ok": True, "version": VERSION, "auth": auth_config()}


@router.post("/standalone/v1/auth/session/anonymous")
def anonymous_session_route(req: AnonymousSessionRequest):
    return create_anonymous_session(req)


@router.post("/standalone/v1/auth/session/verify")
def verify_session_route(req: SessionTokenRequest):
    return verify_session(req.token)


@router.post("/standalone/v1/auth/session/refresh")
def refresh_session_route(req: RefreshSessionRequest):
    return refresh_session(req)


@router.get("/standalone/v1/auth/session/me")
def session_me_route(authorization: Optional[str] = Header(default=None)):
    payload = require_session(authorization)
    return {
        "ok": True,
        "schema": SESSION_SCHEMA,
        "version": VERSION,
        "session": _public_session(payload),
        "wordpressRequired": False,
    }
