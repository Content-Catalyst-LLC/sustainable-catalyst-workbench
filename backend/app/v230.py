"""Workbench v2.3.0 robotics, controls, and mechatronics API routes."""
from __future__ import annotations
from datetime import datetime, timezone
from math import pi, sqrt, isfinite
from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "2.3.0"
router = APIRouter(prefix="/api/v2.3", tags=["workbench-v2.3"])
def utc_now() -> str: return datetime.now(timezone.utc).isoformat()

class KinematicsRequest(BaseModel):
    wheel_diameter_mm: float = Field(gt=0)
    track_width_mm: float = Field(gt=0)
    left_rpm: float
    right_rpm: float
    payload_kg: float = Field(default=0, ge=0)

class ControlRequest(BaseModel):
    kp: float = Field(ge=0); ki: float = Field(ge=0); kd: float = Field(ge=0)
    plant_gain: float = 1.0
    tau: float = Field(default=1.0, gt=0)
    setpoint: float = 1.0
    duration: float = Field(default=10.0, gt=0, le=120)
    dt: float = Field(default=0.02, ge=0.001, le=0.1)

class MechatronicsRequest(BaseModel):
    system_name: str = Field(min_length=1, max_length=120)
    supply_v: float = Field(gt=0)
    current_budget_a: float = Field(gt=0)
    controller: str = Field(min_length=1, max_length=200)
    sensors: list[str] = Field(default_factory=list)
    actuators: list[str] = Field(default_factory=list)
    safety: list[str] = Field(default_factory=list)

class ActuatorRequest(BaseModel):
    actuator_type: Literal['dc-motor','stepper','servo','linear'] = 'dc-motor'
    mass_kg: float = Field(gt=0); radius_m: float = Field(gt=0)
    acceleration: float = Field(ge=0); friction: float = Field(ge=0)
    safety_factor: float = Field(default=2, ge=1); target_rpm: float = Field(gt=0)
    voltage: float = Field(gt=0); efficiency: float = Field(default=.75, gt=0, le=1)

class Transition(BaseModel):
    source: str; event: str; target: str
class StateMachineRequest(BaseModel):
    states: list[str] = Field(min_length=1)
    initial_state: str
    transitions: list[Transition] = Field(default_factory=list)
    safe_states: list[str] = Field(default_factory=list)

class TelemetrySample(BaseModel):
    time: float; setpoint: float; measured: float; current: float; temp: float
class HILRequest(BaseModel):
    samples: list[TelemetrySample] = Field(min_length=1)
    tolerance: float = Field(ge=0)
    max_current: float = Field(gt=0)
    max_temp: float
    min_samples: int = Field(default=4, ge=1)

@router.get('/status')
def status() -> dict[str, object]:
    return {'ok': True, 'version': VERSION, 'studio': 'Robotics, Controls, and Mechatronics', 'capabilities': ['differential-drive-kinematics','pid-baseline-simulation','mechatronics-architecture-review','actuator-sizing','state-machine-validation','hil-telemetry-evaluation']}

@router.post('/robotics/kinematics')
def kinematics(req: KinematicsRequest) -> dict[str, object]:
    diameter=req.wheel_diameter_mm/1000; track=req.track_width_mm/1000
    left=pi*diameter*req.left_rpm/60; right=pi*diameter*req.right_rpm/60
    linear=(left+right)/2; angular=(right-left)/track
    radius=linear/angular if abs(angular)>1e-12 else None
    return {'ok':True,'schema':'sc-workbench-robot-kinematics/1.0','version':VERSION,'generatedAt':utc_now(),'linearSpeedMps':linear,'angularSpeedRadS':angular,'turnRadiusM':radius,'payloadKg':req.payload_kg}

@router.post('/controls/simulate')
def controls(req: ControlRequest) -> dict[str, object]:
    y=0.0; integral=0.0; previous=req.setpoint; peak=float('-inf'); iae=0.0; settling=None; samples=[]
    steps=int(req.duration/req.dt)+1
    for step in range(steps):
        t=step*req.dt; error=req.setpoint-y; integral += error*req.dt; derivative=(error-previous)/req.dt
        command=req.kp*error+req.ki*integral+req.kd*derivative
        y += (req.plant_gain*command-y)/req.tau*req.dt; previous=error; peak=max(peak,y); iae += abs(error)*req.dt
        if len(samples)<1000: samples.append({'time':t,'output':y,'command':command})
        if settling is None and t>req.duration*.1 and abs(error)<=max(abs(req.setpoint)*.02,.001): settling=t
    overshoot=max(0.0,(peak-req.setpoint)/abs(req.setpoint)*100) if req.setpoint else 0.0
    findings=[]
    if overshoot>25: findings.append({'severity':'warning','code':'high-overshoot','valuePercent':overshoot})
    if settling is None: findings.append({'severity':'warning','code':'not-settled'})
    return {'ok':True,'schema':'sc-workbench-control-simulation/1.0','version':VERSION,'generatedAt':utc_now(),'finalOutput':y,'steadyError':req.setpoint-y,'overshootPercent':overshoot,'settlingTimeS':settling,'integralAbsoluteError':iae,'samples':samples,'findings':findings}

@router.post('/mechatronics/review')
def mechatronics(req: MechatronicsRequest) -> dict[str, object]:
    findings=[]
    if not req.sensors: findings.append({'severity':'error','code':'no-sensors'})
    if not req.actuators: findings.append({'severity':'error','code':'no-actuators'})
    if not any(any(token in item.lower() for token in ('stop','watchdog','limit','interlock','fuse')) for item in req.safety): findings.append({'severity':'error','code':'no-explicit-safety-control'})
    return {'ok':not any(f['severity']=='error' for f in findings),'schema':'sc-workbench-mechatronics-architecture/1.0','version':VERSION,'generatedAt':utc_now(),'system':req.model_dump(),'powerBudgetW':req.supply_v*req.current_budget_a,'findings':findings,'reviewGates':['power','interfaces','sensor plausibility','actuator limits','watchdog','safe state','emergency stop','mechanical clearance']}

@router.post('/actuators/size')
def actuator(req: ActuatorRequest) -> dict[str, object]:
    force=(req.mass_kg*req.acceleration+req.mass_kg*9.80665*req.friction)*req.safety_factor
    torque=force*req.radius_m; omega=req.target_rpm*2*pi/60; mechanical=torque*omega; electrical=mechanical/req.efficiency; current=electrical/req.voltage
    return {'ok':True,'schema':'sc-workbench-actuator-sizing/1.0','version':VERSION,'generatedAt':utc_now(),'forceN':force,'torqueNm':torque,'mechanicalPowerW':mechanical,'electricalPowerW':electrical,'estimatedCurrentA':current,'assumptions':req.model_dump()}

@router.post('/state-machines/validate')
def state_machine(req: StateMachineRequest) -> dict[str, object]:
    states=set(req.states); findings=[]
    if len(states)!=len(req.states): findings.append({'severity':'error','code':'duplicate-state'})
    if req.initial_state not in states: findings.append({'severity':'error','code':'unknown-initial-state'})
    reachable={req.initial_state} if req.initial_state in states else set(); changed=True
    while changed:
        changed=False
        for tr in req.transitions:
            if tr.source not in states or tr.target not in states: findings.append({'severity':'error','code':'unknown-transition-state','transition':tr.model_dump()}); continue
            if tr.source in reachable and tr.target not in reachable: reachable.add(tr.target); changed=True
    for state in sorted(states-reachable): findings.append({'severity':'warning','code':'unreachable-state','state':state})
    for state in req.safe_states:
        if state not in states: findings.append({'severity':'error','code':'unknown-safe-state','state':state})
    return {'ok':not any(f['severity']=='error' for f in findings),'schema':'sc-workbench-robot-state-machine/1.0','version':VERSION,'generatedAt':utc_now(),'reachable':sorted(reachable),'findings':findings,'machine':req.model_dump()}

@router.post('/hil/evaluate')
def hil(req: HILRequest) -> dict[str, object]:
    errors=[abs(s.setpoint-s.measured) for s in req.samples]; max_error=max(errors); rmse=sqrt(sum(e*e for e in errors)/len(errors)); max_current=max(s.current for s in req.samples); max_temp=max(s.temp for s in req.samples); findings=[]
    if len(req.samples)<req.min_samples: findings.append({'severity':'error','code':'insufficient-samples'})
    if max_error>req.tolerance: findings.append({'severity':'error','code':'tracking-error','value':max_error})
    if max_current>req.max_current: findings.append({'severity':'error','code':'over-current','value':max_current})
    if max_temp>req.max_temp: findings.append({'severity':'error','code':'over-temperature','value':max_temp})
    return {'ok':not findings,'schema':'sc-workbench-hil-validation/1.0','version':VERSION,'generatedAt':utc_now(),'sampleCount':len(req.samples),'trackingRmse':rmse,'maximumError':max_error,'maximumCurrentA':max_current,'maximumTemperatureC':max_temp,'findings':findings}
