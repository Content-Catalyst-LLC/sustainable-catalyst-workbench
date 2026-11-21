"""ERW 1.3.8.1.6: append-only, owner-scoped bibliographic/evidence snapshots.
Requires existing ERW v1.3.2 source storage and Workbench saved-calculation authority.
No PDF mutation, no autonomous scientific classification or text extraction.
"""
from __future__ import annotations
import hashlib
import math
import re
from typing import Literal, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from .erw_v121 import owner_from_auth
from .erw_v110 import project_for
from .erw_v132_sources import CitationFields, harvard, source_record, storage
from .v1220 import SavedCalculationCreateRequest, save_calculation, list_calculations, get_calculation
from .v510 import content_hash
from .erw_v010 import PROJECT_KEY

VERSION = '1.3.8.1.6'
PREFIX = '/erw/v1.3.8.1.6'
BIB_SCHEMA = 'sc.erw.bibliography.v1.3.8.1.6'
EVIDENCE_SCHEMA = 'sc.erw.evidence.v1.3.8.1.6'
router = APIRouter(tags=['erw-bibliography-evidence'])

class BibliographyRequest(BaseModel):
    sourceId: str = Field(min_length=20,max_length=100)
    citation: CitationFields
    sourceType: Literal['field-experiment','pilot-study','modeling-study','review','government-report','legislation','other'] = 'other'
    abstractNotes: str = Field(default='',max_length=6000)
    researchRelevance: str = Field(default='',max_length=3000)
    keywords: list[str] = Field(default_factory=list,max_length=40)
    reviewNote: str = Field(default='',max_length=2000)
    @field_validator('keywords')
    @classmethod
    def strip_keywords(cls, words):
        return [w.strip() for w in words if w.strip()]

class NumericObservation(BaseModel):
    value: float
    unit: str = Field(min_length=1,max_length=100)
    uncertainty: Optional[float] = Field(default=None,ge=0)
    uncertaintyType: Optional[Literal['SD','SE','CI95','range-half-width','unspecified']] = None
    sampleSize: Optional[int] = Field(default=None,ge=1)
    statistic: Literal['observed','reported-potential','model-output','derived'] = 'observed'
    @field_validator('value','uncertainty')
    @classmethod
    def finite_only(cls, value):
        if value is not None and not math.isfinite(value): raise ValueError('finite numeric values required')
        return value
    @model_validator(mode='after')
    def uncertainty_consistency(self):
        if self.uncertainty is not None and self.uncertaintyType is None:
            raise ValueError('uncertaintyType required when uncertainty supplied')
        return self

class EvidenceRequest(BaseModel):
    sourceId: str = Field(min_length=20,max_length=100)
    claim: str = Field(min_length=8,max_length=5000)
    pdfPage: int = Field(ge=1)
    printedPage: str = Field(default='',max_length=30)
    locator: str = Field(default='',max_length=100)
    exactExcerpt: str = Field(default='',max_length=1500)
    type: Literal['finding','method','limitation','assumption','policy','comparison','knowledge-gap'] = 'finding'
    evidenceStatus: Literal['researcher-entered','researcher-reviewed'] = 'researcher-entered'
    material: str = Field(default='',max_length=120)
    studyLocation: str = Field(default='',max_length=200)
    studyDuration: str = Field(default='',max_length=120)
    applicationRate: Optional[NumericObservation] = None
    soilPH: Optional[NumericObservation] = None
    particleSize: Optional[NumericObservation] = None
    soilDepth: Optional[NumericObservation] = None
    measurement: Optional[NumericObservation] = None
    variable: str = Field(default='',max_length=150)
    observationDate: str = Field(default='',max_length=40)
    method: str = Field(default='',max_length=500)
    controls: str = Field(default='',max_length=500)
    confounders: str = Field(default='',max_length=1000)
    modelRole: Literal['not-applicable','context','candidate-parameter','scenario-boundary','validation-comparator'] = 'not-applicable'
    interpretation: str = Field(default='',max_length=2000)
    warnings: list[str] = Field(default_factory=list,max_length=25)
    linksToEvidence: list[str] = Field(default_factory=list,max_length=25)
    @field_validator('linksToEvidence')
    @classmethod
    def unique_links(cls, links):
        if len(links)!=len(set(links)): raise ValueError('duplicate evidence links')
        return links

def _persist(project_id,owner,kind,source,detail):
    project_for(project_id, owner)
    obj={'schema':BIB_SCHEMA if kind=='bibliography' else EVIDENCE_SCHEMA,
         'researchId':PROJECT_KEY,'projectId':project_id,
         'sourceId':source['sourceId'],'sourceSha256':source['sha256'],
         'recordKind':kind,'details':detail,
         'researcherReviewed': bool(detail.get('citation',{}).get('verifiedByResearcher')) if kind=='bibliography' else detail.get('evidenceStatus')=='researcher-reviewed',
         'externalVerification':False,'verifiedCDR':False,
         'netDurableAtmosphericRemoval':None,'publicationEnabled':False}
    obj['calculationObjectHash']=content_hash(obj)
    request=SavedCalculationCreateRequest(projectId=project_id,
        title=f'ERW {kind}: '+(detail.get('citation',{}).get('title') or detail.get('claim','')[:100]),
        calculationObject=obj,tags=['erw',kind,'research-evidence'],metadata={'researchId':PROJECT_KEY})
    saved=save_calculation(request,owner)
    return {'ok':True,'recordId':saved['id'],'sourceId':source['sourceId'],
            'sourceSha256':source['sha256'],'immutableSnapshot':True}

def _verified_source(project_id,source_id,owner):
    source=source_record(source_id,project_id,owner)
    path=storage(owner,project_id,source['documentId'])
    if not path.is_file(): raise HTTPException(409,detail='Linked PDF is missing')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
        raise HTTPException(409,detail='Linked PDF integrity mismatch')
    return dict(source,sourceId=source_id)

def _records(project_id,owner,kind=None,source_id=None):
    project_for(project_id,owner)
    out=[]
    for row in list_calculations(project_id,owner):
        obj=row.get('calculationObject',{})
        if obj.get('schema') not in (BIB_SCHEMA,EVIDENCE_SCHEMA):continue
        if obj.get('calculationObjectHash')!=content_hash({k:v for k,v in obj.items() if k!='calculationObjectHash'}):
            raise HTTPException(409,detail='Evidence record integrity mismatch')
        if kind and obj['recordKind']!=kind:continue
        if source_id and obj['sourceId']!=source_id:continue
        out.append({'id':row['id'],**obj})
    return out

@router.get(PREFIX+'/status')
def status():
    return {'ok':True,'version':VERSION,'appendOnly':True,'pdfIntegrityVerified':True,
            'automaticEvidenceExtraction':False,'automaticScientificVerification':False}

@router.post(PREFIX+'/projects/{project_id}/bibliography')
def create_bibliography(project_id:str,req:BibliographyRequest,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    source=_verified_source(project_id,req.sourceId,owner)
    citation=harvard(req.citation)
    if req.citation.verifiedByResearcher and not citation.get('reference'):
        raise HTTPException(422,detail='Incomplete approved citation')
    payload=req.model_dump()
    payload['harvard']=citation
    return _persist(project_id,owner,'bibliography',source,payload)

@router.post(PREFIX+'/projects/{project_id}/evidence')
def create_evidence(project_id:str,req:EvidenceRequest,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    source=_verified_source(project_id,req.sourceId,owner)
    linked={row['id'] for row in _records(project_id,owner,kind='evidence')}
    if any(x not in linked for x in req.linksToEvidence):
        raise HTTPException(422,detail='Cross-evidence link must reference an existing project evidence record')
    return _persist(project_id,owner,'evidence',source,req.model_dump())

@router.get(PREFIX+'/projects/{project_id}/records')
def list_records(project_id:str,sourceId:Optional[str]=None,kind:Optional[Literal['bibliography','evidence']]=None,
                 authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    rows=_records(project_id,owner,kind,sourceId)
    return {'ok':True,'count':len(rows),'records':rows}

@router.get(PREFIX+'/projects/{project_id}/records/{record_id}')
def get_record(project_id:str,record_id:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    project_for(project_id,owner)
    row=get_calculation(record_id,owner)
    if row.get('projectId')!=project_id:raise HTTPException(404,detail='Record does not belong to project')
    obj=row.get('calculationObject',{})
    if obj.get('schema') not in (BIB_SCHEMA,EVIDENCE_SCHEMA):raise HTTPException(404,detail='Not a scientific source record')
    if obj.get('calculationObjectHash')!=content_hash({k:v for k,v in obj.items() if k!='calculationObjectHash'}):
        raise HTTPException(409,detail='Record integrity mismatch')
    return {'ok':True,'id':row['id'],'record':obj}

@router.get(PREFIX+'/projects/{project_id}/graph')
def evidence_graph(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    rows=_records(project_id,owner)
    nodes={}
    edges=[]
    for r in rows:
        sid=r['sourceId']
        nodes[sid]={'id':sid,'type':'pdf-source','pdfPath':f'/erw/v1.3.2/projects/{project_id}/sources/{sid}/pdf'}
        nodes[r['id']]={'id':r['id'],'type':r['recordKind'],'reviewed':r['researcherReviewed']}
        edges.append({'from':r['id'],'to':sid,'type':'supported-by-document','sourceSha256':r['sourceSha256']})
        if r['recordKind']=='evidence':
            for target in r['details'].get('linksToEvidence',[]):
                edges.append({'from':r['id'],'to':target,'type':'researcher-linked'})
    return {'ok':True,'nodes':list(nodes.values()),'edges':edges,'computedAgreementOrContradiction':False,
            'automaticInference':False}
