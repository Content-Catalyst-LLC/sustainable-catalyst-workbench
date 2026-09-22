"""Workbench v7.0.0 — Unified Scientific & Engineering Execution Runtime.

v7.0 consolidates the bounded specialist engines already present in Workbench
behind one canonical execution contract.  The runtime validates a declared
operation, dispatches only to an allow-listed in-process specialist function,
wraps the specialist output in a deterministic result/provenance envelope, and
can prepare Platform Core computation-lineage persistence plans.

It does not accept arbitrary Python, shell commands, dynamic imports, arbitrary
callables, hidden output substitution, automatic Core persistence, automatic
remote dispatch, or automatic scientific/truth certification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Optional, Type

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import (
    ComputeInput, CalculusInput, SolveInput, SubstituteInput,
    compute_math, calculus_math, solve_math, substitute_math, content_hash,
)
from .v560 import (
    RootInput, IntegrationInput, DifferentiationInput, InterpolationInput, ODEInput,
    LinearAlgebraInput, OptimizationInput,
    root_object, integration_object, differentiation_object, interpolation_object,
    ode_object, linear_algebra_object, optimization_object,
)
from .v570 import (
    SpectrumInput, ConvolutionInput, FilterDesignInput, TransferFunctionInput,
    StateSpaceInput, PIDInput, RootLocusInput,
    spectrum_object, convolution_object, filter_design_object, transfer_function_object,
    state_space_object, pid_object, root_locus_object,
)
from .v580 import (
    ResistorNetworkInput, RLCInput, ADCDACInput, PWMTimerInput, SamplingInput,
    BusPlanInput, SensorModelInput, GPIOPlanInput, PrototypeScaffoldInput,
    resistor_network_object, rlc_object, adc_dac_object, pwm_timer_object,
    sampling_object, bus_plan_object, sensor_model_object, gpio_plan_object,
    prototype_scaffold_object,
)
from .v590 import (
    BooleanExpressionInput, KarnaughInput, FSMInput, TimingInput, HDLScaffoldInput,
    ResourceEstimateInput, PYNQOverlayInput,
    truth_table_object, minimize_object, karnaugh_object, fsm_object, timing_object,
    hdl_scaffold_object, resource_estimate_object, pynq_overlay_object,
)
from .v230 import (
    KinematicsRequest, ControlRequest, MechatronicsRequest, ActuatorRequest,
    StateMachineRequest, HILRequest,
    kinematics, controls, mechatronics, actuator, state_machine, hil,
)
from .v240 import (
    InstrumentationRequest, AcquisitionRequest, SignalRequest, FrequencyRequest,
    CalibrationRequest as MeasurementCalibrationRequest, MeasurementRequest,
    instrumentation, acquisition, signals, frequency, calibration as measurement_calibration,
    measurements,
)
from .v250 import (
    SimulationRequest, TwinRequest, SystemsRequest, SweepRequest,
    MonteCarloRequest, ValidationRequest,
    run_simulation, evaluate_twin, simulate_system, sweep_scenarios,
    run_monte_carlo, validate_model,
)
from .v680 import (
    SamplingDesignRequest, SobolAnalysisRequest, MorrisAnalysisRequest,
    EnsembleStatisticsRequest, ExceedanceRequest,
    run_sampling_design, run_sobol_analysis, run_morris_analysis,
    run_ensemble_statistics, run_exceedance,
)
from .v6100 import (
    ForecastRequest, BacktestRequest, CalibrationRequest as PredictiveCalibrationRequest,
    execute_forecast, execute_backtest, execute_calibration,
)
from .v6110 import (
    TrajectoryReconstructionRequest, TemporalComparisonRequest,
    UncertaintyPropagationRequest, HypothesisMetricsRequest,
    execute_trajectory, execute_temporal_comparison, execute_uncertainty,
    execute_hypothesis_metrics,
)
from .energy_workbench_runtime import execute as execute_energy_handoff
from .v640 import CORE_RUNTIME_CONTRACT, _authorize_core_route
from .v660 import CORE_UNIFIED_RUNTIME_CONTRACT
from .v670 import (
    CORE_COMPUTATION_LINEAGE_CONTRACT,
    ExecutionCreateRequest, ExecutionComponentsRequest,
    InputItem, ParameterItem, EnvironmentItem, StepItem, OutputItem,
    build_execution_create, build_components,
)
from .v6140 import CORE_CERTIFICATION_CONTRACT

VERSION = APP_VERSION
SCHEMA = "sc-workbench-unified-scientific-engineering-execution-runtime/1.0"
RESULT_SCHEMA = "sc-workbench-unified-execution-result/1.0"
WORKFLOW_SCHEMA = "sc-workbench-unified-execution-workflow/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-unified-execution-core-lineage-plan/1.0"
CORE_LINEAGE_CONTRACT_TARGET = "sc.research.computation-analysis-execution-lineage.v1"
RUNTIME_REF = "workbench:/runtime/unified-scientific-engineering-execution"
router = APIRouter(tags=["workbench-v700-unified-scientific-engineering-execution"])


@dataclass(frozen=True)
class OperationSpec:
    key: str
    category: str
    source_release: str
    execution_type: str
    output_type: str
    model: Optional[Type[BaseModel]]
    executor: Callable[[Any], Dict[str, Any]]
    deterministic: bool = True
    description: str = ""


def _energy_executor(payload: Dict[str, Any]) -> Dict[str, Any]:
    return execute_energy_handoff(payload)


def _spec(key: str, category: str, release: str, execution_type: str, output_type: str,
          model: Optional[Type[BaseModel]], executor: Callable[[Any], Dict[str, Any]], description: str = "") -> OperationSpec:
    return OperationSpec(key, category, release, execution_type, output_type, model, executor, True, description)


OPERATIONS: Dict[str, OperationSpec] = {
    # Symbolic mathematics / CAS
    "math.compute": _spec("math.compute", "mathematics", "5.1.0", "engineering_calculation", "statistic", ComputeInput, compute_math),
    "math.calculus": _spec("math.calculus", "mathematics", "5.1.0", "engineering_calculation", "statistic", CalculusInput, calculus_math),
    "math.solve": _spec("math.solve", "mathematics", "5.1.0", "engineering_calculation", "result_bundle", SolveInput, solve_math),
    "math.substitute": _spec("math.substitute", "mathematics", "5.1.0", "engineering_calculation", "statistic", SubstituteInput, substitute_math),

    # Numerical scientific computing
    "numerical.root": _spec("numerical.root", "numerical-scientific", "5.6.0", "engineering_calculation", "statistic", RootInput, root_object),
    "numerical.integrate": _spec("numerical.integrate", "numerical-scientific", "5.6.0", "engineering_calculation", "statistic", IntegrationInput, integration_object),
    "numerical.differentiate": _spec("numerical.differentiate", "numerical-scientific", "5.6.0", "engineering_calculation", "statistic", DifferentiationInput, differentiation_object),
    "numerical.interpolate": _spec("numerical.interpolate", "numerical-scientific", "5.6.0", "engineering_calculation", "table", InterpolationInput, interpolation_object),
    "numerical.ode": _spec("numerical.ode", "numerical-scientific", "5.6.0", "simulation", "result_bundle", ODEInput, ode_object),
    "numerical.linear-algebra": _spec("numerical.linear-algebra", "numerical-scientific", "5.6.0", "engineering_calculation", "result_bundle", LinearAlgebraInput, linear_algebra_object),
    "numerical.optimize": _spec("numerical.optimize", "numerical-scientific", "5.6.0", "optimization", "result_bundle", OptimizationInput, optimization_object),

    # Simulation / systems modeling
    "simulation.dynamic": _spec("simulation.dynamic", "simulation-systems", "2.5.0", "simulation", "result_bundle", SimulationRequest, run_simulation),
    "simulation.digital-twin": _spec("simulation.digital-twin", "simulation-systems", "2.5.0", "simulation", "result_bundle", TwinRequest, evaluate_twin),
    "simulation.state-space-system": _spec("simulation.state-space-system", "simulation-systems", "2.5.0", "simulation", "result_bundle", SystemsRequest, simulate_system),
    "simulation.parameter-sweep": _spec("simulation.parameter-sweep", "simulation-systems", "2.5.0", "simulation", "table", SweepRequest, sweep_scenarios),
    "simulation.monte-carlo": _spec("simulation.monte-carlo", "simulation-systems", "2.5.0", "simulation", "result_bundle", MonteCarloRequest, run_monte_carlo),
    "model.validate": _spec("model.validate", "simulation-systems", "2.5.0", "statistical_analysis", "report", ValidationRequest, validate_model),

    # Robotics / controls / mechatronics
    "robotics.kinematics": _spec("robotics.kinematics", "controls-mechatronics", "2.3.0", "engineering_calculation", "result_bundle", KinematicsRequest, kinematics),
    "controls.pid-baseline": _spec("controls.pid-baseline", "controls-mechatronics", "2.3.0", "simulation", "result_bundle", ControlRequest, controls),
    "mechatronics.review": _spec("mechatronics.review", "controls-mechatronics", "2.3.0", "engineering_calculation", "report", MechatronicsRequest, mechatronics),
    "actuator.size": _spec("actuator.size", "controls-mechatronics", "2.3.0", "engineering_calculation", "result_bundle", ActuatorRequest, actuator),
    "state-machine.validate": _spec("state-machine.validate", "controls-mechatronics", "2.3.0", "engineering_calculation", "report", StateMachineRequest, state_machine),
    "hil.evaluate": _spec("hil.evaluate", "controls-mechatronics", "2.3.0", "engineering_calculation", "report", HILRequest, hil),

    # Measurement / instrumentation
    "instrumentation.review": _spec("instrumentation.review", "measurement-instrumentation", "2.4.0", "engineering_calculation", "report", InstrumentationRequest, instrumentation),
    "acquisition.plan": _spec("acquisition.plan", "measurement-instrumentation", "2.4.0", "engineering_calculation", "report", AcquisitionRequest, acquisition),
    "measurement.signal-analyze": _spec("measurement.signal-analyze", "measurement-instrumentation", "2.4.0", "statistical_analysis", "result_bundle", SignalRequest, signals),
    "measurement.frequency-analyze": _spec("measurement.frequency-analyze", "measurement-instrumentation", "2.4.0", "statistical_analysis", "result_bundle", FrequencyRequest, frequency),
    "measurement.calibrate": _spec("measurement.calibrate", "measurement-instrumentation", "2.4.0", "statistical_analysis", "report", MeasurementCalibrationRequest, measurement_calibration),
    "measurement.validate": _spec("measurement.validate", "measurement-instrumentation", "2.4.0", "statistical_analysis", "report", MeasurementRequest, measurements),

    # Signals / systems / control mathematics
    "signals.spectrum": _spec("signals.spectrum", "signals-controls", "5.7.0", "statistical_analysis", "result_bundle", SpectrumInput, spectrum_object),
    "signals.convolve": _spec("signals.convolve", "signals-controls", "5.7.0", "engineering_calculation", "result_bundle", ConvolutionInput, convolution_object),
    "signals.filter-design": _spec("signals.filter-design", "signals-controls", "5.7.0", "engineering_calculation", "model", FilterDesignInput, filter_design_object),
    "controls.transfer-function": _spec("controls.transfer-function", "signals-controls", "5.7.0", "engineering_calculation", "result_bundle", TransferFunctionInput, transfer_function_object),
    "controls.state-space": _spec("controls.state-space", "signals-controls", "5.7.0", "simulation", "result_bundle", StateSpaceInput, state_space_object),
    "controls.pid": _spec("controls.pid", "signals-controls", "5.7.0", "simulation", "result_bundle", PIDInput, pid_object),
    "controls.root-locus": _spec("controls.root-locus", "signals-controls", "5.7.0", "engineering_calculation", "result_bundle", RootLocusInput, root_locus_object),

    # Electronics / embedded systems
    "electronics.resistor-network": _spec("electronics.resistor-network", "electronics-embedded", "5.8.0", "engineering_calculation", "result_bundle", ResistorNetworkInput, resistor_network_object),
    "electronics.rlc": _spec("electronics.rlc", "electronics-embedded", "5.8.0", "engineering_calculation", "result_bundle", RLCInput, rlc_object),
    "electronics.adc-dac": _spec("electronics.adc-dac", "electronics-embedded", "5.8.0", "engineering_calculation", "result_bundle", ADCDACInput, adc_dac_object),
    "electronics.pwm-timer": _spec("electronics.pwm-timer", "electronics-embedded", "5.8.0", "engineering_calculation", "result_bundle", PWMTimerInput, pwm_timer_object),
    "electronics.sampling": _spec("electronics.sampling", "electronics-embedded", "5.8.0", "engineering_calculation", "report", SamplingInput, sampling_object),
    "embedded.bus-plan": _spec("embedded.bus-plan", "electronics-embedded", "5.8.0", "engineering_calculation", "report", BusPlanInput, bus_plan_object),
    "embedded.sensor-model": _spec("embedded.sensor-model", "electronics-embedded", "5.8.0", "engineering_calculation", "result_bundle", SensorModelInput, sensor_model_object),
    "embedded.gpio-plan": _spec("embedded.gpio-plan", "electronics-embedded", "5.8.0", "engineering_calculation", "report", GPIOPlanInput, gpio_plan_object),
    "embedded.prototype-scaffold": _spec("embedded.prototype-scaffold", "electronics-embedded", "5.8.0", "engineering_calculation", "artifact", PrototypeScaffoldInput, prototype_scaffold_object),

    # Digital logic / FPGA
    "digital.truth-table": _spec("digital.truth-table", "digital-logic-fpga", "5.9.0", "engineering_calculation", "table", BooleanExpressionInput, truth_table_object),
    "digital.minimize": _spec("digital.minimize", "digital-logic-fpga", "5.9.0", "engineering_calculation", "result_bundle", BooleanExpressionInput, minimize_object),
    "digital.karnaugh": _spec("digital.karnaugh", "digital-logic-fpga", "5.9.0", "engineering_calculation", "result_bundle", KarnaughInput, karnaugh_object),
    "digital.fsm": _spec("digital.fsm", "digital-logic-fpga", "5.9.0", "engineering_calculation", "report", FSMInput, fsm_object),
    "digital.timing": _spec("digital.timing", "digital-logic-fpga", "5.9.0", "engineering_calculation", "result_bundle", TimingInput, timing_object),
    "digital.hdl-scaffold": _spec("digital.hdl-scaffold", "digital-logic-fpga", "5.9.0", "engineering_calculation", "artifact", HDLScaffoldInput, hdl_scaffold_object),
    "digital.resource-estimate": _spec("digital.resource-estimate", "digital-logic-fpga", "5.9.0", "engineering_calculation", "report", ResourceEstimateInput, resource_estimate_object),
    "digital.pynq-overlay": _spec("digital.pynq-overlay", "digital-logic-fpga", "5.9.0", "engineering_calculation", "artifact", PYNQOverlayInput, pynq_overlay_object),

    # Uncertainty / sensitivity
    "uncertainty.sampling-design": _spec("uncertainty.sampling-design", "uncertainty-sensitivity", "6.8.0", "statistical_analysis", "dataset", SamplingDesignRequest, run_sampling_design),
    "uncertainty.sobol": _spec("uncertainty.sobol", "uncertainty-sensitivity", "6.8.0", "statistical_analysis", "statistic", SobolAnalysisRequest, run_sobol_analysis),
    "uncertainty.morris": _spec("uncertainty.morris", "uncertainty-sensitivity", "6.8.0", "statistical_analysis", "statistic", MorrisAnalysisRequest, run_morris_analysis),
    "uncertainty.ensemble": _spec("uncertainty.ensemble", "uncertainty-sensitivity", "6.8.0", "statistical_analysis", "statistic", EnsembleStatisticsRequest, run_ensemble_statistics),
    "uncertainty.exceedance": _spec("uncertainty.exceedance", "uncertainty-sensitivity", "6.8.0", "statistical_analysis", "statistic", ExceedanceRequest, run_exceedance),

    # Predictive intelligence
    "predictive.forecast": _spec("predictive.forecast", "predictive", "6.10.0", "forecasting", "forecast", ForecastRequest, execute_forecast),
    "predictive.backtest": _spec("predictive.backtest", "predictive", "6.10.0", "statistical_analysis", "report", BacktestRequest, execute_backtest),
    "predictive.calibration": _spec("predictive.calibration", "predictive", "6.10.0", "statistical_analysis", "report", PredictiveCalibrationRequest, execute_calibration),

    # Forensic quantitative reconstruction
    "forensics.trajectory": _spec("forensics.trajectory", "forensic-quantitative", "6.11.0", "forensic_reconstruction", "result_bundle", TrajectoryReconstructionRequest, execute_trajectory),
    "forensics.temporal-comparison": _spec("forensics.temporal-comparison", "forensic-quantitative", "6.11.0", "forensic_reconstruction", "result_bundle", TemporalComparisonRequest, execute_temporal_comparison),
    "forensics.uncertainty": _spec("forensics.uncertainty", "forensic-quantitative", "6.11.0", "forensic_reconstruction", "statistic", UncertaintyPropagationRequest, execute_uncertainty),
    "forensics.hypothesis-metrics": _spec("forensics.hypothesis-metrics", "forensic-quantitative", "6.11.0", "forensic_reconstruction", "report", HypothesisMetricsRequest, execute_hypothesis_metrics),

    # Energy runtime retains its explicit handoff contract as the payload.
    "energy.execute-handoff": _spec("energy.execute-handoff", "energy-systems", "6.3.0", "engineering_calculation", "result_bundle", None, _energy_executor),
}


class UnifiedExecutionRequest(BaseModel):
    operation: str = Field(min_length=1, max_length=180)
    payload: Dict[str, Any] = Field(default_factory=dict)
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    requestKey: str = Field(default="", max_length=180)
    label: str = Field(default="", max_length=400)
    inputRefs: List[str] = Field(default_factory=list, max_length=200)
    tags: List[str] = Field(default_factory=list, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("operation")
    @classmethod
    def operation_known(cls, value: str) -> str:
        key = value.strip()
        if key not in OPERATIONS:
            raise ValueError(f"Unsupported unified execution operation: {key}")
        return key


class WorkflowStep(BaseModel):
    stepId: str = Field(min_length=1, max_length=120)
    operation: str = Field(min_length=1, max_length=180)
    payload: Dict[str, Any] = Field(default_factory=dict)
    dependsOn: List[str] = Field(default_factory=list, max_length=50)
    label: str = Field(default="", max_length=400)
    inputRefs: List[str] = Field(default_factory=list, max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("operation")
    @classmethod
    def operation_known(cls, value: str) -> str:
        key = value.strip()
        if key not in OPERATIONS:
            raise ValueError(f"Unsupported unified execution operation: {key}")
        return key


class WorkflowRequest(BaseModel):
    workflowKey: str = Field(default="workbench-unified-workflow", min_length=1, max_length=180)
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    steps: List[WorkflowStep] = Field(min_length=1, max_length=50)
    stopOnFailure: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_graph(self):
        ids = [step.stepId for step in self.steps]
        if len(set(ids)) != len(ids):
            raise ValueError("workflow stepId values must be unique")
        known = set(ids)
        for step in self.steps:
            unknown = sorted(set(step.dependsOn) - known)
            if unknown:
                raise ValueError(f"step {step.stepId} depends on unknown steps: {', '.join(unknown)}")
            if step.stepId in step.dependsOn:
                raise ValueError(f"step {step.stepId} may not depend on itself")
        return self


class CoreLineagePlanRequest(BaseModel):
    executionResult: Dict[str, Any]
    coreExecutionId: str = Field(default="", max_length=128)
    coreSessionId: str = Field(default="", max_length=128)
    projectRef: str = Field(default="", max_length=1000)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)


def _bounded_list(values: List[str], limit: int = 1000) -> List[str]:
    return sorted({str(x).strip()[:limit] for x in values if str(x).strip()})


def _operation_record(spec: OperationSpec) -> Dict[str, Any]:
    return {
        "key": spec.key,
        "category": spec.category,
        "sourceRelease": spec.source_release,
        "executionType": spec.execution_type,
        "runtimeKind": "workbench",
        "outputType": spec.output_type,
        "inputModel": spec.model.__name__ if spec.model else "explicit-energy-handoff",
        "deterministic": spec.deterministic,
        "description": spec.description,
    }


def execution_manifest() -> Dict[str, Any]:
    categories = sorted({spec.category for spec in OPERATIONS.values()})
    record = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Unified Scientific & Engineering Execution Runtime",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "runtimeRef": RUNTIME_REF,
        "operationCount": len(OPERATIONS),
        "categories": categories,
        "coreContracts": {
            "runtime": CORE_RUNTIME_CONTRACT,
            "unifiedResearchRuntime": CORE_UNIFIED_RUNTIME_CONTRACT,
            "computationLineage": CORE_COMPUTATION_LINEAGE_CONTRACT,
            "integrationCertification": CORE_CERTIFICATION_CONTRACT,
        },
        "capabilities": {
            "canonicalExecutionEnvelope": True,
            "allowlistedSpecialistDispatch": True,
            "deterministicExecutionIdentity": True,
            "contentHashedInputsAndResults": True,
            "workflowExecution": True,
            "dependencyOrderedWorkflow": True,
            "coreLineagePlanning": True,
            "symbolicMathematics": True,
            "numericalScientificComputing": True,
            "simulationAndSystems": True,
            "measurementAndInstrumentation": True,
            "signalsAndControls": True,
            "electronicsAndEmbedded": True,
            "digitalLogicAndFpga": True,
            "uncertaintyAndSensitivity": True,
            "predictiveIntelligence": True,
            "forensicQuantitativeReconstruction": True,
            "energySystemsExplicitInputExecution": True,
        },
        "boundaries": {
            "arbitraryPythonExecutionAuthorized": False,
            "shellExecutionAuthorized": False,
            "dynamicImportAuthorized": False,
            "arbitraryCallableUploadAuthorized": False,
            "hiddenWorkflowOutputSubstitutionAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "automaticScientificValidityCertification": False,
            "automaticTruthDetermination": False,
            "automaticRecommendationOrRanking": False,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


def execution_catalog() -> Dict[str, Any]:
    ops = [_operation_record(OPERATIONS[key]) for key in sorted(OPERATIONS)]
    categories: Dict[str, List[str]] = {}
    for item in ops:
        categories.setdefault(item["category"], []).append(item["key"])
    out = {
        "ok": True,
        "schema": "sc-workbench-unified-execution-operation-catalog/1.0",
        "version": VERSION,
        "runtimeRef": RUNTIME_REF,
        "operationCount": len(ops),
        "operations": ops,
        "categories": categories,
    }
    out["catalogHash"] = content_hash(out)
    return out


def _stable_result_basis(value: Any) -> Any:
    """Remove diagnostic timestamps before deterministic scientific-result hashing."""
    volatile = {"generatedAt", "createdAt", "updatedAt", "observedAt", "timestamp", "timestampUtc"}
    if isinstance(value, dict):
        return {k: _stable_result_basis(v) for k, v in sorted(value.items()) if k not in volatile}
    if isinstance(value, list):
        return [_stable_result_basis(v) for v in value]
    return value


def _validate_payload(spec: OperationSpec, payload: Dict[str, Any]) -> Any:
    if spec.model is None:
        if not isinstance(payload, dict) or not payload:
            raise ValueError("energy.execute-handoff requires the complete explicit Energy Systems handoff payload")
        return payload
    return spec.model.model_validate(payload)


def _execute_request(request: UnifiedExecutionRequest) -> Dict[str, Any]:
    spec = OPERATIONS[request.operation]
    stable_request = {
        "operation": request.operation,
        "payload": request.payload,
        "projectRef": request.projectRef,
        "coreSessionId": request.coreSessionId,
        "requestKey": request.requestKey,
        "label": request.label,
        "inputRefs": _bounded_list(request.inputRefs),
        "tags": _bounded_list(request.tags, 180),
        "metadata": request.metadata,
    }
    request_hash = content_hash(stable_request)
    execution_id = "wbe-" + content_hash({"runtime": SCHEMA, "request": stable_request})[:24]
    execution_ref = f"sc://workbench/execution/{execution_id}"
    try:
        validated = _validate_payload(spec, request.payload)
        raw_result = spec.executor(validated)
    except HTTPException:
        raise
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail={"operation": request.operation, "validationErrors": exc.errors()}) from exc
    except (ValueError, TypeError, ArithmeticError) as exc:
        raise HTTPException(status_code=422, detail={"operation": request.operation, "error": str(exc)}) from exc
    result_hash = content_hash(_stable_result_basis(raw_result))
    output_ref = f"{execution_ref}/result/{result_hash[:16]}"
    result = {
        "ok": bool(raw_result.get("ok", True)) if isinstance(raw_result, dict) else True,
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "runtimeRef": RUNTIME_REF,
        "executionId": execution_id,
        "executionRef": execution_ref,
        "requestKey": request.requestKey or execution_id,
        "label": request.label or request.operation,
        "operation": request.operation,
        "category": spec.category,
        "executionType": spec.execution_type,
        "runtimeKind": "workbench",
        "sourceRelease": spec.source_release,
        "deterministicOperation": spec.deterministic,
        "projectRef": request.projectRef,
        "coreSessionId": request.coreSessionId,
        "inputRefs": _bounded_list(request.inputRefs),
        "outputRef": output_ref,
        "outputType": spec.output_type,
        "requestHash": request_hash,
        "resultHash": result_hash,
        "result": raw_result,
        "provenance": {
            "product": PRODUCT_KEY,
            "workbenchVersion": VERSION,
            "runtimeRef": RUNTIME_REF,
            "specialistSourceRelease": spec.source_release,
            "operation": request.operation,
            "inputContentHash": content_hash(request.payload),
            "resultContentHash": result_hash,
        },
        "lineageHints": {
            "executionType": spec.execution_type,
            "runtimeKind": "workbench",
            "workbenchExecutionRef": execution_ref,
            "inputRefs": _bounded_list(request.inputRefs),
            "outputRefs": [output_ref],
        },
        "boundaries": {
            "specialistComputationPerformedByWorkbench": True,
            "arbitraryCodeExecuted": False,
            "automaticCoreDispatchPerformed": False,
            "automaticCorePersistencePerformed": False,
            "scientificValidityCertified": False,
            "truthDetermined": False,
            "recommendationOrRankingPerformedByUnifiedRuntime": False,
        },
    }
    result["executionEnvelopeHash"] = content_hash(result)
    return result


def _workflow_order(steps: List[WorkflowStep]) -> List[WorkflowStep]:
    by_id = {s.stepId: s for s in steps}
    indegree = {s.stepId: len(set(s.dependsOn)) for s in steps}
    children: Dict[str, List[str]] = {s.stepId: [] for s in steps}
    for step in steps:
        for dep in set(step.dependsOn):
            children[dep].append(step.stepId)
    queue = sorted([sid for sid, degree in indegree.items() if degree == 0])
    ordered: List[WorkflowStep] = []
    while queue:
        sid = queue.pop(0)
        ordered.append(by_id[sid])
        for child in sorted(children[sid]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
                queue.sort()
    if len(ordered) != len(steps):
        cyclic = sorted(sid for sid, degree in indegree.items() if degree > 0)
        raise ValueError("workflow dependency cycle detected: " + ", ".join(cyclic))
    return ordered


def execute_workflow(request: WorkflowRequest) -> Dict[str, Any]:
    try:
        ordered = _workflow_order(request.steps)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    results: List[Dict[str, Any]] = []
    result_refs: Dict[str, str] = {}
    failed_step = ""
    for step in ordered:
        try:
            item = _execute_request(UnifiedExecutionRequest(
                operation=step.operation,
                payload=step.payload,
                projectRef=request.projectRef,
                coreSessionId=request.coreSessionId,
                requestKey=f"{request.workflowKey}:{step.stepId}",
                label=step.label or step.stepId,
                inputRefs=step.inputRefs,
                metadata={"workflowKey": request.workflowKey, "stepId": step.stepId, "dependsOn": step.dependsOn, **step.metadata},
            ))
            item["workflowStepId"] = step.stepId
            item["dependsOn"] = list(step.dependsOn)
            item["dependencyResultRefs"] = [result_refs[x] for x in step.dependsOn if x in result_refs]
            results.append(item)
            result_refs[step.stepId] = item["outputRef"]
            if not item.get("ok", True) and request.stopOnFailure:
                failed_step = step.stepId
                break
        except HTTPException as exc:
            results.append({
                "ok": False,
                "schema": RESULT_SCHEMA,
                "version": VERSION,
                "workflowStepId": step.stepId,
                "operation": step.operation,
                "error": exc.detail,
            })
            failed_step = step.stepId
            if request.stopOnFailure:
                break
    completed = len([x for x in results if x.get("ok")])
    record = {
        "ok": not failed_step,
        "schema": WORKFLOW_SCHEMA,
        "version": VERSION,
        "runtimeRef": RUNTIME_REF,
        "workflowKey": request.workflowKey,
        "projectRef": request.projectRef,
        "coreSessionId": request.coreSessionId,
        "declaredStepCount": len(request.steps),
        "executedStepCount": len(results),
        "completedStepCount": completed,
        "dependencyOrder": [s.stepId for s in ordered],
        "failedStepId": failed_step or None,
        "results": results,
        "resultRefs": result_refs,
        "automaticOutputSubstitutionPerformed": False,
        "automaticCoreDispatchPerformed": False,
        "automaticCorePersistencePerformed": False,
    }
    record["workflowHash"] = content_hash({
        "workflowKey": request.workflowKey,
        "projectRef": request.projectRef,
        "steps": [s.model_dump() for s in request.steps],
        "resultHashes": [x.get("resultHash") for x in results if x.get("resultHash")],
    })
    return record


def _require_unified_result(value: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema") != RESULT_SCHEMA:
        raise ValueError(f"executionResult must use {RESULT_SCHEMA}")
    if value.get("version") != VERSION:
        raise ValueError(f"executionResult version must be {VERSION}")
    if not value.get("executionRef") or not value.get("resultHash"):
        raise ValueError("executionResult is missing execution identity or result hash")
    return value


def build_core_lineage_plan(request: CoreLineagePlanRequest) -> Dict[str, Any]:
    try:
        result = _require_unified_result(request.executionResult)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    project_ref = request.projectRef or str(result.get("projectRef") or "")
    session_id = request.coreSessionId or str(result.get("coreSessionId") or "")
    create_plan = build_execution_create(ExecutionCreateRequest(
        executionKey=str(result["executionId"]),
        title=str(result.get("label") or result.get("operation")),
        executionType=result.get("executionType", "engineering_calculation"),
        runtimeKind="workbench",
        status="completed",
        visibility=request.visibility,
        projectRef=project_ref,
        coreSessionId=session_id,
        workbenchExecutionRef=str(result["executionRef"]),
        methodPlanRef=f"{RUNTIME_REF}/operation/{result['operation']}",
        commandOrEntrypoint=str(result["operation"]),
        provenance={"workbenchExecutionEnvelopeHash": result.get("executionEnvelopeHash"), "requestHash": result.get("requestHash")},
        metadata={"unifiedExecutionRuntime": SCHEMA, "resultHash": result.get("resultHash"), "sourceRelease": result.get("sourceRelease")},
        createdBy=request.createdBy,
    ))
    component_plan = None
    if request.coreExecutionId:
        component_plan = build_components(ExecutionComponentsRequest(
            coreExecutionId=request.coreExecutionId,
            coreSessionId=session_id,
            projectRef=project_ref,
            workbenchExecutionRef=str(result["executionRef"]),
            runtime="workbench",
            methodRef=f"{RUNTIME_REF}/operation/{result['operation']}",
            visibility=request.visibility,
            inputs=[InputItem(
                inputKey="unified-execution-input",
                inputType="other",
                objectRef=f"{result['executionRef']}/input",
                contentHash=str(result.get("requestHash") or ""),
                role="execution-input",
                selector={"operation": result.get("operation")},
                provenance={"inputRefs": result.get("inputRefs", [])},
                createdBy=request.createdBy,
            )],
            parameters=[ParameterItem(
                parameterKey="operation",
                value={"operation": result.get("operation"), "category": result.get("category")},
                sourceRef=RUNTIME_REF,
                provenance={"sourceRelease": result.get("sourceRelease")},
                createdBy=request.createdBy,
            )],
            environments=[EnvironmentItem(
                environmentKey="workbench-unified-runtime",
                environmentType="workbench",
                runtimeName="Sustainable Catalyst Workbench",
                runtimeVersion=VERSION,
                environmentHash=content_hash({"runtime": SCHEMA, "version": VERSION, "operation": result.get("operation")}),
                provenance={"runtimeRef": RUNTIME_REF},
                createdBy=request.createdBy,
            )],
            steps=[StepItem(
                stepKey="specialist-execution",
                sequence=1,
                stepType=str(result.get("category") or "specialist-computation"),
                toolRef=RUNTIME_REF,
                operationText=str(result.get("operation")),
                inputRefs=list(result.get("inputRefs") or []),
                outputRefs=[str(result.get("outputRef"))],
                parameters={"requestHash": result.get("requestHash"), "resultHash": result.get("resultHash")},
                provenance={"executionEnvelopeHash": result.get("executionEnvelopeHash")},
                createdBy=request.createdBy,
            )],
            outputs=[OutputItem(
                outputKey="unified-execution-result",
                outputType=result.get("outputType", "result_bundle"),
                objectRef=str(result.get("outputRef")),
                contentHash=str(result.get("resultHash") or ""),
                schema={"schema": RESULT_SCHEMA, "specialistResultSchema": (result.get("result") or {}).get("schema") if isinstance(result.get("result"), dict) else None},
                metadata={"operation": result.get("operation"), "category": result.get("category"), "sourceRelease": result.get("sourceRelease")},
                provenance={"workbenchExecutionRef": result.get("executionRef")},
                createdBy=request.createdBy,
            )],
        ))
    plan = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "runtimeRef": RUNTIME_REF,
        "coreRuntimeContract": CORE_RUNTIME_CONTRACT,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "executionRegistration": create_plan,
        "lineageComponents": component_plan,
        "coreExecutionIdProvided": bool(request.coreExecutionId),
        "coreExecutionIdMustComeFromCore": not bool(request.coreExecutionId),
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "scientificValidityCertified": False,
        "reproducibilityInferred": False,
    }
    plan["planHash"] = content_hash(plan)
    return plan


@router.get("/execution/runtime/manifest")
def manifest() -> Dict[str, Any]:
    return execution_manifest()


@router.get("/execution/runtime/catalog")
def catalog() -> Dict[str, Any]:
    return execution_catalog()


@router.post("/execution/runtime/execute")
def execute(request: UnifiedExecutionRequest) -> Dict[str, Any]:
    return _execute_request(request)


@router.post("/execution/runtime/workflow/run")
def workflow_run(request: WorkflowRequest) -> Dict[str, Any]:
    return execute_workflow(request)


@router.post("/integration/core/unified-execution/lineage/plan")
def core_lineage_plan(
    request: CoreLineagePlanRequest,
    x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return build_core_lineage_plan(request)


@router.get("/v700/status")
def status() -> Dict[str, Any]:
    manifest = execution_manifest()
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Unified Scientific & Engineering Execution Runtime",
        "runtimeRef": RUNTIME_REF,
        "operationCount": manifest["operationCount"],
        "categoryCount": len(manifest["categories"]),
        "canonicalExecutionEnvelope": True,
        "workflowExecution": True,
        "coreLineagePlanning": True,
        "allowlistedSpecialistDispatch": True,
        "arbitraryCodeExecution": False,
        "automaticCoreDispatch": False,
        "automaticCorePersistence": False,
        "scientificValidityCertification": False,
        "truthDetermination": False,
    }
