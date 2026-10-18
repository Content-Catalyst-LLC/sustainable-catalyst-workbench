"""ERW 1.2.1 — restricted Sustainable Catalyst standalone identity onboarding.

Uses Workbench's signed bearer sessions and project persistence. WordPress is not
an identity authority. Account enrollment requires a server-side key and durable
session secret. Anonymous certification projects are never reassigned.
"""
from __future__ import annotations
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from . import v1210
from .erw_v010 import PROJECT_KEY, template
from .v1220 import create_project, ProjectCreateRequest
from .erw_v110 import projects_for
from .release import APP_VERSION

router=APIRouter(tags=["erw-1.2.1-standalone-identity"])
ITERATIONS=600_000
MAX_FAILURES=5
LOCK_SECONDS=900
USERNAME_RE=re.compile(r"^[a-z][a-z0-9_.-]{2,47}$")
class Enroll(BaseModel):
    username:str=Field(min_length=3,max_length=48)
    password:str=Field(min_length=14,max_length=256)
    enrollmentKey:str=Field(min_length=12,max_length=256)
class Login(BaseModel):
    username:str=Field(min_length=3,max_length=48)
    password:str=Field(min_length=1,max_length=256)
class Onboard(BaseModel):
    confirmHypothetical:bool=False

def configured():
    if len(os.getenv("SCWB_SESSION_SECRET",""))<32:
        raise HTTPException(503,detail="Durable session signing secret not configured")
    if len(os.getenv("SCWB_IDENTITY_ENROLLMENT_KEY",""))<24:
        raise HTTPException(503,detail="Enrollment disabled until server configuration")
def path():
    return Path(os.getenv("SCWB_IDENTITY_DB_PATH","/data/scwb-identity-v121.sqlite3"))
@contextmanager
def database():
    p=path()
    p.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(str(p),timeout=20)
    c.row_factory=sqlite3.Row
    try:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("""CREATE TABLE IF NOT EXISTS identities(
            id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
            salt BLOB NOT NULL, password_hash BLOB NOT NULL,
            failed INTEGER NOT NULL DEFAULT 0, locked_until INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL)""")
        c.commit()
        yield c
        c.commit()
    finally:c.close()
def username(raw):
    n=raw.strip().lower()
    if not USERNAME_RE.fullmatch(n):
        raise HTTPException(422,detail="Invalid username format")
    return n
def password_hash(password,salt):
    return hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),salt,ITERATIONS)
def enroll(req:Enroll):
    configured()
    if not hmac.compare_digest(req.enrollmentKey,os.environ["SCWB_IDENTITY_ENROLLMENT_KEY"]):
        raise HTTPException(403,detail="Enrollment not authorized")
    name=username(req.username)
    salt=secrets.token_bytes(32)
    digest=password_hash(req.password,salt)
    uid="sc:"+str(uuid.uuid4())
    try:
        with database() as c:
            c.execute("INSERT INTO identities(id,username,salt,password_hash,created_at) VALUES(?,?,?,?,?)",
                      (uid,name,salt,digest,int(time.time())))
    except sqlite3.IntegrityError:
        raise HTTPException(409,detail="Account already exists")
    return {"ok":True,"identityId":uid,"username":name,"wordpressRequired":False}
def login(req:Login):
    configured()
    name=username(req.username)
    with database() as c:
        row=c.execute("SELECT * FROM identities WHERE username=?",(name,)).fetchone()
        if row is None:
            password_hash(req.password,b"0"*32)
            raise HTTPException(401,detail="Invalid credentials")
        now=int(time.time())
        if row["locked_until"]>now:raise HTTPException(429,detail="Account temporarily locked")
        valid=hmac.compare_digest(password_hash(req.password,row["salt"]),row["password_hash"])
        if not valid:
            failures=int(row["failed"])+1
            until=now+LOCK_SECONDS if failures>=MAX_FAILURES else 0
            c.execute("UPDATE identities SET failed=?,locked_until=? WHERE id=?",(failures,until,row["id"]))
            raise HTTPException(401,detail="Invalid credentials")
        c.execute("UPDATE identities SET failed=0,locked_until=0 WHERE id=?",(row["id"],))
        uid=row["id"]
    now=int(time.time())
    payload={"schema":v1210.SESSION_SCHEMA,"version":APP_VERSION,
        "audience":v1210.PRODUCT_KEY,"sessionId":str(uuid.uuid4()),
        "subject":{"type":"sustainable-catalyst-account","id":uid,"authenticated":True},
        "roles":["researcher"],"capabilities":["calculation:execute","graph:view","project:read","project:write","research:author"],
        "authProvider":"sustainable-catalyst-identity","issuedAt":now,
        "expiresAt":now+3600,"sessionGeneration":1,"clientLabel":"erw-report-workspace"}
    return {"ok":True,"token":v1210._sign_payload(payload),"tokenType":"Bearer",
            "session":v1210._public_session(payload),"wordpressRequired":False}
def owner_from_auth(authorization):
    session=v1210.require_session(authorization)
    subject=session.get("subject",{})
    if subject.get("type")!="sustainable-catalyst-account" or subject.get("authenticated") is not True:
        raise HTTPException(403,detail="Sustainable Catalyst account required")
    return subject["id"]
@router.get("/erw/v1.2.1/status")
def status():
    return {"ok":True,"extensionVersion":"1.2.1","identityAuthority":"sustainable-catalyst",
            "wordpressRequired":False,"enrollmentConfigured":len(os.getenv("SCWB_IDENTITY_ENROLLMENT_KEY",""))>=24,
            "durableSigningConfigured":len(os.getenv("SCWB_SESSION_SECRET",""))>=32,
            "crossProductSSO":False,"legacySessionMigration":False,"publicationEnabled":False}
@router.post("/erw/v1.2.1/identity/enroll")
def enroll_route(req:Enroll):return enroll(req)
@router.post("/erw/v1.2.1/identity/login")
def login_route(req:Login):return login(req)
@router.get("/erw/v1.2.1/identity/me")
def me_route(authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    return {"ok":True,"identityId":owner,"projectCount":len(projects_for(owner))}
@router.post("/erw/v1.2.1/onboard/wexford")
def onboard_route(req:Onboard,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    if not req.confirmHypothetical:raise HTTPException(422,detail="Explicit hypothetical-study confirmation required")
    existing=projects_for(owner)
    for p in existing:
        if p.get("metadata",{}).get("onboardingKey")=="wexford-erw-v121":
            return {"ok":True,"project":p,"created":False}
    project=create_project(ProjectCreateRequest(
        name=template()["title"],
        description=template()["researchQuestion"],
        metadata={"researchId":PROJECT_KEY,"onboardingKey":"wexford-erw-v121",
                  "evidenceClass":"hypothetical","publicationEnabled":False}),owner)
    return {"ok":True,"project":project,"created":True}
@router.get("/erw/v1.2.1/onboarding",response_class=HTMLResponse)
def onboarding_ui():return HTMLResponse(PAGE)
PAGE=r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sustainable Catalyst · Research Onboarding</title><style>
body{margin:0;background:#0d0d0d;color:#f4f4f4;font:16px system-ui}main{max-width:850px;margin:40px auto;padding:36px;border:1px solid #444;border-radius:12px;background:#171717}h1{letter-spacing:.05em}h1 em{color:#e43f42;font-style:normal}p{color:#ccc;line-height:1.55}label{display:block;margin:16px 0 5px}input{display:block;width:100%;box-sizing:border-box;padding:12px;font:inherit;background:#222;color:white;border:1px solid #666;border-radius:5px}button{margin-top:16px;padding:13px 19px;background:#cf2d35;color:white;border:0;border-radius:5px;cursor:pointer;font-weight:700}button.secondary{background:#383838}.notice{border-left:3px solid #e43f42;padding:12px;background:#282020}#status{white-space:pre-wrap;color:#e9e9e9;margin-top:20px}a{color:#fff}</style></head><body><main><h1>SUSTAINABLE <em>CATALYST</em></h1><h2>Research Identity &amp; Project Onboarding</h2><p>Sign in to your standalone Sustainable Catalyst account. Research objects remain in Workbench, independent of WordPress. Account creation is currently invitation-only.</p><p class="notice">Wexford is a hypothetical project. Earlier certification projects owned by different sessions will not transfer automatically. No carbon removal is verified.</p>
<label>Username</label><input id="username" autocomplete="username">
<label>Password</label><input id="password" type="password" autocomplete="current-password">
<label>Enrollment key (only when creating an account)</label><input id="key" type="password" autocomplete="off">
<button id="enroll" class="secondary">Create account</button> <button id="login">Sign in</button><div id="onboarding" hidden><button id="create">Create/open Wexford research project</button><p>After onboarding, open the report workspace. You will still need an authenticated handoff; the legacy editor does not yet share this new login automatically.</p></div>
<p id="status" role="status"></p></main><script>
(()=>{'use strict';const e=id=>document.getElementById(id);let bearer='';
async function request(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json',...(bearer?{'Authorization':'Bearer '+bearer}:{})},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Request failed');return d}
function error(x){e('status').textContent=x.message||String(x)}
e('enroll').onclick=async()=>{try{await request('/erw/v1.2.1/identity/enroll',{username:e('username').value,password:e('password').value,enrollmentKey:e('key').value});e('key').value='';e('status').textContent='Account created. Select Sign in.'}catch(x){error(x)}};
e('login').onclick=async()=>{try{const d=await request('/erw/v1.2.1/identity/login',{username:e('username').value,password:e('password').value});bearer=d.token;e('password').value='';e('key').value='';e('onboarding').hidden=false;e('status').textContent='Signed in. Token retained in this browser tab only. No WordPress login required.'}catch(x){error(x)}};
e('create').onclick=async()=>{try{const d=await request('/erw/v1.2.1/onboard/wexford',{confirmHypothetical:true});e('status').textContent='Wexford project ready: '+d.project.id+'. No external evidence imported and no verified CDR.'}catch(x){error(x)}};
})();
</script></body></html>"""
