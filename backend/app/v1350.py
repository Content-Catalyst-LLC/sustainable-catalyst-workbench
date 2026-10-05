"""Workbench v13.5.0 — Interactive Graph Studio."""
from __future__ import annotations
import json, sqlite3, time, uuid
from typing import Any, Dict, List, Optional, Literal
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v11160 import GraphingRequest, execute_graphing
from .v1220 import _connection, _owner, _assert_project_owner, _json
from .v1340 import get_research_session, project_workspace_contract

VERSION=APP_VERSION
router=APIRouter(tags=["workbench-v1350-interactive-graph-studio"])
GRAPH_SCHEMA="sc-workbench-graph-studio-object/1.0"
ANNOTATION_SCHEMA="sc-workbench-graph-annotation/1.0"
STATUS_SCHEMA="sc-workbench-interactive-graph-studio-status/1.0"

class GraphSeriesSpec(BaseModel):
    expression:str=Field(min_length=1,max_length=20000)
    label:Optional[str]=Field(default=None,max_length=240)
    variable:str=Field(default="x",max_length=100)
    visible:bool=True
    includeRoots:bool=True
    includeCriticalPoints:bool=True
    includeDerivative:bool=False
    includeIntegral:bool=False

class GraphStudioCreateRequest(BaseModel):
    projectId:str=Field(min_length=1,max_length=100)
    researchSessionId:Optional[str]=Field(default=None,max_length=100)
    title:str=Field(default="Graph Study",min_length=1,max_length=240)
    graphType:Literal["cartesian","parametric","polar","implicit"]="cartesian"
    series:List[GraphSeriesSpec]=Field(default_factory=list,max_length=24)
    domain:List[float]=Field(default_factory=lambda:[-10.0,10.0],min_length=2,max_length=2)
    yDomain:List[float]=Field(default_factory=lambda:[-10.0,10.0],min_length=2,max_length=2)
    samples:int=Field(default=401,ge=25,le=5000)
    metadata:Dict[str,Any]=Field(default_factory=dict)

class GraphStudioUpdateRequest(BaseModel):
    title:Optional[str]=Field(default=None,min_length=1,max_length=240)
    series:Optional[List[GraphSeriesSpec]]=None
    domain:Optional[List[float]]=Field(default=None,min_length=2,max_length=2)
    yDomain:Optional[List[float]]=Field(default=None,min_length=2,max_length=2)
    samples:Optional[int]=Field(default=None,ge=25,le=5000)
    metadata:Optional[Dict[str,Any]]=None

class AnnotationRequest(BaseModel):
    kind:Literal["point","vertical-line","horizontal-line","note"]="note"
    label:str=Field(min_length=1,max_length=500)
    x:Optional[float]=None
    y:Optional[float]=None
    metadata:Dict[str,Any]=Field(default_factory=dict)

def _hash(x:Any)->str:
    return content_hash(x)

def _migrate(conn:sqlite3.Connection)->None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS scwb_graph_studies(
      id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL,
      research_session_id TEXT,
      owner_subject TEXT NOT NULL,
      title TEXT NOT NULL,
      graph_type TEXT NOT NULL,
      series_json TEXT NOT NULL DEFAULT '[]',
      domain_json TEXT NOT NULL,
      y_domain_json TEXT NOT NULL,
      samples INTEGER NOT NULL,
      metadata_json TEXT NOT NULL DEFAULT '{}',
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL,
      FOREIGN KEY(project_id) REFERENCES scwb_projects(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_scwb_graph_studies_project
      ON scwb_graph_studies(project_id,owner_subject,updated_at DESC);

    CREATE TABLE IF NOT EXISTS scwb_graph_annotations(
      id TEXT PRIMARY KEY,
      graph_id TEXT NOT NULL,
      owner_subject TEXT NOT NULL,
      kind TEXT NOT NULL,
      label TEXT NOT NULL,
      x REAL,
      y REAL,
      metadata_json TEXT NOT NULL DEFAULT '{}',
      created_at INTEGER NOT NULL,
      FOREIGN KEY(graph_id) REFERENCES scwb_graph_studies(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_scwb_graph_annotations_graph
      ON scwb_graph_annotations(graph_id,owner_subject,created_at);
    """)

def _graph_row(conn,graph_id,owner):
    row=conn.execute("SELECT * FROM scwb_graph_studies WHERE id=? AND owner_subject=?",
                     (graph_id,owner)).fetchone()
    if row is None:
        raise HTTPException(status_code=404,detail="Graph study not found")
    return row

def _annotation_dict(row):
    return {"schema":ANNOTATION_SCHEMA,"id":row["id"],"graphId":row["graph_id"],
            "kind":row["kind"],"label":row["label"],"x":row["x"],"y":row["y"],
            "metadata":_json(row["metadata_json"],{}),"createdAt":row["created_at"]}

def _graph_dict(row,annotations=None):
    body={"schema":GRAPH_SCHEMA,"id":row["id"],"projectId":row["project_id"],
          "researchSessionId":row["research_session_id"],"title":row["title"],
          "graphType":row["graph_type"],"series":_json(row["series_json"],[]),
          "domain":_json(row["domain_json"],[-10.0,10.0]),
          "yDomain":_json(row["y_domain_json"],[-10.0,10.0]),
          "samples":row["samples"],"metadata":_json(row["metadata_json"],{}),
          "createdAt":row["created_at"],"updatedAt":row["updated_at"],
          "annotations":annotations or []}
    body["graphObjectHash"]=_hash(body)
    return body

def create_graph(req,owner):
    if not req.series:
        raise HTTPException(status_code=422,detail="At least one graph series is required")
    now=int(time.time()); gid=str(uuid.uuid4())
    with _connection() as conn:
        _migrate(conn); _assert_project_owner(conn,req.projectId,owner)
        if req.researchSessionId:
            rs=get_research_session(req.researchSessionId,owner)
            if rs["projectId"]!=req.projectId:
                raise HTTPException(status_code=409,detail="Research session belongs to another project")
        conn.execute("""INSERT INTO scwb_graph_studies
          (id,project_id,research_session_id,owner_subject,title,graph_type,series_json,
           domain_json,y_domain_json,samples,metadata_json,created_at,updated_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (gid,req.projectId,req.researchSessionId,owner,req.title.strip(),req.graphType,
           json.dumps([x.model_dump() for x in req.series],sort_keys=True),
           json.dumps(req.domain),json.dumps(req.yDomain),req.samples,
           json.dumps(req.metadata,sort_keys=True),now,now))
        row=_graph_row(conn,gid,owner)
    return _graph_dict(row)

def list_graphs(project_id,owner):
    with _connection() as conn:
        _migrate(conn); _assert_project_owner(conn,project_id,owner)
        rows=conn.execute("""SELECT * FROM scwb_graph_studies
          WHERE project_id=? AND owner_subject=? ORDER BY updated_at DESC,id""",
          (project_id,owner)).fetchall()
    return [_graph_dict(r) for r in rows]

def get_graph(graph_id,owner):
    with _connection() as conn:
        _migrate(conn); row=_graph_row(conn,graph_id,owner)
        ann=conn.execute("""SELECT * FROM scwb_graph_annotations
          WHERE graph_id=? AND owner_subject=? ORDER BY created_at,id""",
          (graph_id,owner)).fetchall()
    return _graph_dict(row,[_annotation_dict(a) for a in ann])

def update_graph(graph_id,req,owner):
    with _connection() as conn:
        _migrate(conn); cur=_graph_row(conn,graph_id,owner); now=int(time.time())
        title=req.title.strip() if req.title is not None else cur["title"]
        series=json.dumps([x.model_dump() for x in req.series],sort_keys=True) if req.series is not None else cur["series_json"]
        domain=json.dumps(req.domain) if req.domain is not None else cur["domain_json"]
        ydomain=json.dumps(req.yDomain) if req.yDomain is not None else cur["y_domain_json"]
        samples=req.samples if req.samples is not None else cur["samples"]
        meta=json.dumps(req.metadata,sort_keys=True) if req.metadata is not None else cur["metadata_json"]
        conn.execute("""UPDATE scwb_graph_studies SET title=?,series_json=?,domain_json=?,
          y_domain_json=?,samples=?,metadata_json=?,updated_at=? WHERE id=? AND owner_subject=?""",
          (title,series,domain,ydomain,samples,meta,now,graph_id,owner))
        row=_graph_row(conn,graph_id,owner)
    return _graph_dict(row)

def delete_graph(graph_id,owner):
    with _connection() as conn:
        _migrate(conn); _graph_row(conn,graph_id,owner)
        conn.execute("DELETE FROM scwb_graph_studies WHERE id=? AND owner_subject=?",(graph_id,owner))
    return {"ok":True,"deletedGraphId":graph_id}

def add_annotation(graph_id,req,owner):
    now=int(time.time()); aid=str(uuid.uuid4())
    with _connection() as conn:
        _migrate(conn); _graph_row(conn,graph_id,owner)
        conn.execute("""INSERT INTO scwb_graph_annotations
          (id,graph_id,owner_subject,kind,label,x,y,metadata_json,created_at)
          VALUES (?,?,?,?,?,?,?,?,?)""",
          (aid,graph_id,owner,req.kind,req.label,req.x,req.y,
           json.dumps(req.metadata,sort_keys=True),now))
        row=conn.execute("SELECT * FROM scwb_graph_annotations WHERE id=?",(aid,)).fetchone()
    return _annotation_dict(row)

def render_graph(graph_id,owner):
    graph=get_graph(graph_id,owner)
    rendered=[]
    if graph["graphType"]=="cartesian":
        for i,s in enumerate(graph["series"]):
            if not s.get("visible",True):
                continue
            req=GraphingRequest(
                operation="linked-function-study" if (
                    s.get("includeDerivative") or s.get("includeIntegral")
                ) else "function-plot",
                expression=s["expression"],
                variable=s.get("variable","x"),
                domain=graph["domain"],
                yDomain=graph["yDomain"],
                samples=graph["samples"],
                includeRoots=s.get("includeRoots",True),
                includeCriticalPoints=s.get("includeCriticalPoints",True),
                includeDerivative=s.get("includeDerivative",False),
                includeIntegral=s.get("includeIntegral",False),
                linkGroup=f"graph-{graph_id}"
            )
            result=execute_graphing(req)
            for view in result["result"]["views"]:
                view["graphSeriesIndex"]=i
                view["graphSeriesLabel"]=s.get("label") or s["expression"]
                rendered.append(view)
    else:
        raise HTTPException(status_code=422,detail="v13.5 persistent studio currently executes saved cartesian studies; other v11.16 graph types remain available through the renderer bridge")
    body={"schema":"sc-workbench-graph-studio-render/1.0","version":VERSION,
          "graph":graph,"views":rendered,"viewCount":len(rendered),
          "renderer":"standalone-svg-view-renderer/1.0",
          "viewSpecAuthority":"v11.16 backend","wordpressRequired":False}
    body["renderHash"]=_hash(body)
    return body

def studio_contract():
    prior=project_workspace_contract()
    features={"persistentGraphObjects":True,"multipleFunctionSeries":True,
      "savedDomainsAndSampling":True,"rootAndCriticalPointControls":True,
      "derivativeAndIntegralLinkedViews":True,"graphAnnotations":True,
      "projectBinding":True,"researchSessionBinding":True,"sessionActivityHandoff":True,
      "rendererNeutralViewSpecs":True,"backendSamplingAuthority":True,
      "wordpressRequiredFalse":True}
    body={"schema":"sc-workbench-interactive-graph-studio-contract/1.0",
          "version":VERSION,"v134ProjectWorkspacePreserved":all(prior["features"].values()),
          "features":features,"wordpressRequired":False}
    body["contractHash"]=_hash(body); return body

def status():
    c=studio_contract()
    checks={"v134WorkspacePreserved":c["v134ProjectWorkspacePreserved"],
            "graphStudioReady":all(c["features"].values()),
            "backendViewSpecAuthority":True,
            "wordpressRequiredFalse":c["wordpressRequired"] is False}
    return {"ok":all(checks.values()),"schema":STATUS_SCHEMA,"version":VERSION,
      "release":"Interactive Graph Studio","product":PRODUCT_KEY,"name":PRODUCT_NAME,
      "runtime":RUNTIME_KIND,"wordpressRequired":False,
      "graphStudioReady":all(checks.values()),"checks":checks,
      "contractHash":c["contractHash"]}

@router.get("/v1350/status")
def status_route(): return status()

@router.get("/standalone/v1/graph-studio/contract")
def contract_route(): return {"ok":True,"version":VERSION,"graphStudio":studio_contract()}

@router.post("/standalone/v1/graph-studio/graphs")
def create_route(req:GraphStudioCreateRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"graph":create_graph(req,owner)}

@router.get("/standalone/v1/projects/{project_id}/graphs")
def list_route(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); items=list_graphs(project_id,owner)
    return {"ok":True,"version":VERSION,"graphs":items,"count":len(items)}

@router.get("/standalone/v1/graph-studio/graphs/{graph_id}")
def get_route(graph_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"graph":get_graph(graph_id,owner)}

@router.patch("/standalone/v1/graph-studio/graphs/{graph_id}")
def patch_route(graph_id:str,req:GraphStudioUpdateRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"graph":update_graph(graph_id,req,owner)}

@router.delete("/standalone/v1/graph-studio/graphs/{graph_id}")
def delete_route(graph_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return delete_graph(graph_id,owner)

@router.post("/standalone/v1/graph-studio/graphs/{graph_id}/annotations")
def annotation_route(graph_id:str,req:AnnotationRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"annotation":add_annotation(graph_id,req,owner)}

@router.post("/standalone/v1/graph-studio/graphs/{graph_id}/render")
def render_route(graph_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"render":render_graph(graph_id,owner)}
