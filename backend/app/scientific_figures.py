"""Source-bound Lab figures in the existing owned research-session activity store."""
import base64
import hashlib
import json
import os
import re
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .v1220 import _owner, _connection
from .v1340 import (get_research_session, append_activity, ResearchSessionActivityRequest,
                    _migrate, _session_row, _activity_dict)

router=APIRouter(prefix='/standalone/v1/research-sessions',tags=['source-bound-scientific-figures'])
class ImportFigure(BaseModel):
    model_config=ConfigDict(extra='forbid')
    artifactId:str=Field(pattern=r'^artifact:sha256:[a-f0-9]{64}$')
    workspaceProjectId:str=Field(min_length=1,max_length=100)

def validate_source(raw):
    try:
        obj=json.loads(raw,parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if obj.get('schema')!='sc-lab-scientific-visualization/1.0': raise ValueError()
        context=obj['scientificContext']
        if not isinstance(context['source']['sha256'],str) or not re.fullmatch('[a-f0-9]{64}',context['source']['sha256']):raise ValueError()
        if not context['unit'] or not context['source']['citation']:raise ValueError()
        if not obj['cells']:raise ValueError()
        return obj
    except (ValueError,KeyError,TypeError,AttributeError):
        raise HTTPException(422,'Expected a source-declared native Lab scientific figure.')

@router.post('/{session_id}/scientific-figures',status_code=201)
def import_figure(session_id:str,body:ImportFigure,authorization:str|None=Header(default=None)):
    owner,_=_owner(authorization)
    session=get_research_session(session_id,owner)
    if session['metadata'].get('workspaceProjectId')!=body.workspaceProjectId:
        raise HTTPException(409,'Research session is not bound to this Workspace project.')
    url=os.getenv('SCWB_LIBRARY_URL','').rstrip('/')
    token=os.getenv('SCWB_LIBRARY_TOKEN','')
    if not url or not token:raise HTTPException(503,'Library integration is not configured.')
    try:
        with httpx.Client(timeout=20,follow_redirects=False,trust_env=False) as client:
            with client.stream('GET',url+'/v1/admin/artifacts/'+quote(body.artifactId,safe='')+'/content',headers={'Authorization':'Bearer '+token}) as r:
                if r.status_code!=200:raise HTTPException(502,'Library artifact retrieval failed.')
                chunks=[];size=0
                for chunk in r.iter_bytes():
                    size+=len(chunk)
                    if size>1_500_000:raise HTTPException(413,'Scientific figure exceeds the handoff limit.')
                    chunks.append(chunk)
                raw=b''.join(chunks)
    except httpx.HTTPError as exc:raise HTTPException(502,'Library is unavailable.') from exc
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=body.artifactId.rsplit(':',1)[1]:raise HTTPException(409,'Library artifact SHA256 mismatch.')
    obj=validate_source(raw)
    metadata={'workspaceProjectId':body.workspaceProjectId,'libraryArtifactId':body.artifactId,
              'sha256':digest,'contentBase64':base64.b64encode(raw).decode(),
              'source':obj['scientificContext']['source'],'revision':1}
    receipt=append_activity(session_id,ResearchSessionActivityRequest(kind='scientific-figure-version',
        label=obj.get('title','Scientific figure'),objectType=obj['schema'],objectId=body.artifactId,
        route='workspace',metadata=metadata),owner)
    return {'figure':receipt}

@router.get('/{session_id}/scientific-figures/{figure_id}')
def get_figure(session_id:str,figure_id:str,authorization:str|None=Header(default=None)):
    owner,_=_owner(authorization)
    with _connection() as conn:
        _migrate(conn);_session_row(conn,session_id,owner)
        row=conn.execute('SELECT * FROM scwb_research_session_activity WHERE id=? AND session_id=? AND owner_subject=? AND kind=?',
            (figure_id,session_id,owner,'scientific-figure-version')).fetchone()
        if row is None:raise HTTPException(404,'Scientific figure version not found.')
        return {'figure':_activity_dict(row)}
