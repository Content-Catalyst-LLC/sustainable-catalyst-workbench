"""Workbench v2.6.0 multi-language engineering runtime routes."""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from statistics import mean, variance
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "2.6.0"
router = APIRouter(prefix="/v260", tags=["workbench-v260"])

LANGUAGE_CATALOG: dict[str, dict[str, Any]] = {
    "python": {"label": "Python", "extension": ".py", "command": "python3", "execution": True},
    "javascript": {"label": "JavaScript / Node.js", "extension": ".js", "command": "node", "execution": True},
    "r": {"label": "R", "extension": ".R", "command": "Rscript", "execution": True},
    "sql": {"label": "SQL / SQLite", "extension": ".sql", "command": "sqlite3", "execution": True},
    "go": {"label": "Go", "extension": ".go", "command": "go", "execution": True},
    "c": {"label": "C11", "extension": ".c", "command": "cc", "execution": True},
    "cpp": {"label": "C++17", "extension": ".cpp", "command": "c++", "execution": True},
    "rust": {"label": "Rust", "extension": ".rs", "command": "rustc", "execution": True},
    "haskell": {"label": "Haskell", "extension": ".hs", "command": "runhaskell", "execution": True},
    "assembly": {"label": "Assembly profile", "extension": ".asm", "command": "nasm", "execution": False},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def canonical_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonical_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonical_json(item) for item in value]
    return value


def normalized_text(value: Any) -> str:
    return "\n".join(line.rstrip() for line in str(value).strip().replace("\r\n", "\n").splitlines())


class EquivalenceRequest(BaseModel):
    calculation: Literal["energy", "quadratic", "dot_product", "linear_regression"] = "energy"
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    absolute_tolerance: float = Field(default=1e-9, ge=0)
    relative_tolerance: float = Field(default=1e-9, ge=0)


class BenchmarkRequest(BaseModel):
    benchmark: Literal["cancellation", "summation", "dot_product"] = "summation"
    values: list[float]
    repeats: int = Field(default=1000, ge=1, le=1_000_000)


class ProjectRequest(BaseModel):
    language: Literal["python", "javascript", "r", "sql", "go", "c", "cpp", "rust", "haskell", "assembly"]
    template: Literal["engineering_calculation", "csv_analysis", "simulation_step", "unit_test"] = "engineering_calculation"
    project_name: str = Field(default="engineering-runtime-example", min_length=1, max_length=80)
    expression: str = Field(default="power_kw * hours", min_length=1, max_length=500)
    dependencies: list[str] = Field(default_factory=list)


class ExecutionRecord(BaseModel):
    language: str
    runtime: str = ""
    output: Any
    duration_ms: float | None = Field(default=None, ge=0)
    exit_code: int = 0


class ReproducibilityRequest(BaseModel):
    records: list[ExecutionRecord]
    comparison_mode: Literal["numeric", "exact", "json"] = "numeric"
    tolerance: float = Field(default=1e-9, ge=0)
    required_languages: list[str] = Field(default_factory=list)


class AuditRequest(BaseModel):
    language: str
    source_bytes: int = Field(ge=0)
    timeout_seconds: float = Field(gt=0)
    output_bytes: int = Field(ge=0)
    filesystem_mode: Literal["temporary", "project", "unrestricted"] = "temporary"
    network_access: Literal["disabled", "required"] = "disabled"
    explicit_consent: bool = False


def expected_calculation(kind: str, inputs: dict[str, Any]) -> Any:
    if kind == "energy":
        return float(inputs.get("power_kw", 0)) * float(inputs.get("hours", 0))
    if kind == "dot_product":
        left = [float(value) for value in inputs.get("left", [])]
        right = [float(value) for value in inputs.get("right", [])]
        return sum(left[index] * right[index] for index in range(min(len(left), len(right))))
    if kind == "quadratic":
        a = float(inputs.get("a", 1))
        b = float(inputs.get("b", 0))
        c = float(inputs.get("c", 0))
        if a == 0:
            return []
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            return []
        root = math.sqrt(discriminant)
        return sorted([(-b - root) / (2 * a), (-b + root) / (2 * a)])
    x = [float(value) for value in inputs.get("x", [])]
    y = [float(value) for value in inputs.get("y", [])]
    count = min(len(x), len(y))
    if count < 2:
        return {"slope": None, "intercept": None}
    x = x[:count]
    y = y[:count]
    mx = mean(x)
    my = mean(y)
    sxx = sum((value - mx) ** 2 for value in x)
    sxy = sum((x[index] - mx) * (y[index] - my) for index in range(count))
    slope = sxy / sxx if sxx else 0.0
    return {"slope": slope, "intercept": my - slope * mx}


def compare_value(actual: Any, expected: Any, absolute: float, relative: float) -> dict[str, Any]:
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return {"pass": False, "reason": "array-shape-mismatch"}
        details = [compare_value(a, e, absolute, relative) for a, e in zip(actual, expected)]
        return {"pass": all(detail["pass"] for detail in details), "details": details}
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return {"pass": False, "reason": "object-shape-mismatch"}
        details = {key: compare_value(actual.get(key), value, absolute, relative) for key, value in expected.items()}
        return {"pass": all(detail["pass"] for detail in details.values()), "details": details}
    actual_number = finite_float(actual)
    expected_number = finite_float(expected)
    if actual_number is None or expected_number is None:
        return {"pass": actual == expected, "actual": actual, "expected": expected}
    absolute_error = abs(actual_number - expected_number)
    relative_error = absolute_error / max(abs(expected_number), 1e-30)
    return {
        "pass": absolute_error <= absolute or relative_error <= relative,
        "actual": actual_number,
        "expected": expected_number,
        "absoluteError": absolute_error,
        "relativeError": relative_error,
    }


@router.get("/runtime/catalog")
def runtime_catalog() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-runtime-catalog/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "languages": LANGUAGE_CATALOG,
        "executionBoundary": {
            "loopbackOnly": True,
            "pairingRequired": True,
            "originBoundTokens": True,
            "arbitraryShellEndpoint": False,
            "maximumSourceBytes": 204800,
            "maximumOutputBytes": 262144,
            "temporaryWorkingDirectory": True,
        },
    }


@router.post("/equivalence/compare")
def compare_equivalence(request: EquivalenceRequest) -> dict[str, Any]:
    expected = expected_calculation(request.calculation, request.inputs)
    comparisons = {
        language: compare_value(value, expected, request.absolute_tolerance, request.relative_tolerance)
        for language, value in request.outputs.items()
    }
    passed = bool(comparisons) and all(record["pass"] for record in comparisons.values())
    return {
        "ok": passed,
        "schema": "sc-workbench-language-equivalence/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "calculation": request.calculation,
        "inputs": request.inputs,
        "expected": expected,
        "tolerances": {"absolute": request.absolute_tolerance, "relative": request.relative_tolerance},
        "comparisons": comparisons,
        "findings": [{"severity": "pass" if passed else "warning", "code": "all-results-equivalent" if passed else "runtime-results-differ"}],
    }


def kahan_sum(values: list[float]) -> float:
    total = 0.0
    correction = 0.0
    for value in values:
        adjusted = value - correction
        next_total = total + adjusted
        correction = (next_total - total) - adjusted
        total = next_total
    return total


def pairwise_sum(values: list[float]) -> float:
    if len(values) < 2:
        return values[0] if values else 0.0
    middle = len(values) // 2
    return pairwise_sum(values[:middle]) + pairwise_sum(values[middle:])


@router.post("/numerical/benchmark")
def numerical_benchmark(request: BenchmarkRequest) -> dict[str, Any]:
    values = [float(value) for value in request.values]
    if not values:
        return {"ok": False, "version": VERSION, "findings": [{"severity": "error", "code": "no-values"}]}
    getcontext().prec = 50
    decimal_reference = sum((Decimal(str(value)) for value in values), Decimal(0))
    naive = sum(values)
    kahan = kahan_sum(values)
    pairwise = pairwise_sum(values)
    methods = {"naive": naive, "kahan": kahan, "pairwise": pairwise}
    errors = {name: float(abs(Decimal(str(value)) - decimal_reference)) for name, value in methods.items()}
    best = min(errors, key=errors.get)
    spread = max(methods.values()) - min(methods.values())
    findings = []
    if spread:
        findings.append({"severity": "warning", "code": "summation-order-sensitive", "methodSpread": spread})
    else:
        findings.append({"severity": "pass", "code": "methods-agree"})
    return {
        "ok": True,
        "schema": "sc-workbench-numerical-benchmark/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "benchmark": request.benchmark,
        "sampleCount": len(values),
        "repeats": request.repeats,
        "results": methods,
        "decimalReference": str(decimal_reference),
        "absoluteErrors": errors,
        "bestMethod": best,
        "sampleVariance": variance(values) if len(values) > 1 else 0.0,
        "findings": findings,
    }


def safe_project_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
    return cleaned or "engineering-runtime-example"


def source_template(language: str, expression: str, project_name: str) -> tuple[str, str]:
    expression = expression.strip()
    project = safe_project_name(project_name)
    records: dict[str, tuple[str, str]] = {
        "python": ("main.py", f'"""{project}: generated Workbench engineering calculation."""\n\ndef calculate(power_kw: float, hours: float) -> float:\n    return {expression}\n\nif __name__ == "__main__":\n    print(f"{{calculate(2.5, 8.0):.12g}}")\n'),
        "javascript": ("main.js", f"'use strict';\nfunction calculate(power_kw, hours) {{ return {expression}; }}\nconsole.log(calculate(2.5, 8.0).toPrecision(12));\n"),
        "r": ("main.R", f"calculate <- function(power_kw, hours) {{ {expression} }}\ncat(format(calculate(2.5, 8.0), digits=12), '\\n')\n"),
        "sql": ("main.sql", f"WITH inputs(power_kw, hours) AS (VALUES (2.5, 8.0))\nSELECT printf('%.12g', {expression}) AS result FROM inputs;\n"),
        "go": ("main.go", f'package main\nimport "fmt"\nfunc calculate(power_kw, hours float64) float64 {{ return {expression} }}\nfunc main(){{ fmt.Printf("%.12g\\n", calculate(2.5,8.0)) }}\n'),
        "c": ("main.c", f'#include <stdio.h>\ndouble calculate(double power_kw,double hours){{ return {expression}; }}\nint main(void){{ printf("%.12g\\n",calculate(2.5,8.0)); return 0; }}\n'),
        "cpp": ("main.cpp", f'#include <iomanip>\n#include <iostream>\ndouble calculate(double power_kw,double hours){{ return {expression}; }}\nint main(){{ std::cout<<std::setprecision(12)<<calculate(2.5,8.0)<<"\\n"; }}\n'),
        "rust": ("main.rs", f'fn calculate(power_kw:f64,hours:f64)->f64{{ {expression} }}\nfn main(){{ println!("{{:.12}}",calculate(2.5,8.0)); }}\n'),
        "haskell": ("main.hs", f"calculate :: Double -> Double -> Double\ncalculate power_kw hours = {expression}\nmain :: IO ()\nmain = print (calculate 2.5 8.0)\n"),
        "assembly": ("main.asm", f"; {project} assembly profile\n; Select x86-64, ARM64, ARMv7, RISC-V, or AVR.\n; Define ABI, numeric representation, calling convention, and test vectors before implementation.\n"),
    }
    return records[language]


@router.post("/projects/generate")
def generate_project(request: ProjectRequest) -> dict[str, Any]:
    filename, source = source_template(request.language, request.expression, request.project_name)
    project = safe_project_name(request.project_name)
    files = {
        filename: source,
        "README.md": f"# {project}\n\nLanguage: {request.language}\nTemplate: {request.template}\nGenerated by Workbench v2.6.0. Validate units, dependencies, numeric precision, compiler/runtime versions, and outputs.\n",
        "test-vectors.json": json.dumps({"schema": "sc-workbench-runtime-test-vectors/1.0", "cases": [{"inputs": {"power_kw": 2.5, "hours": 8.0}, "expected": 20.0}]}, indent=2) + "\n",
    }
    return {
        "ok": True,
        "schema": "sc-workbench-multilanguage-project/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "project": project,
        "language": request.language,
        "template": request.template,
        "dependencies": request.dependencies,
        "files": files,
        "validationChecklist": [
            "Confirm units and data types",
            "Pin runtime and dependency versions",
            "Run supplied test vector",
            "Compare output against a second language",
            "Review overflow, numerical stability, and platform behavior",
        ],
    }


@router.post("/reproducibility/validate")
def validate_reproducibility(request: ReproducibilityRequest) -> dict[str, Any]:
    records = request.records
    present = {record.language for record in records}
    missing = [language for language in request.required_languages if language not in present]
    reference = records[0].output if records else None
    comparisons = []
    for record in records:
        if request.comparison_mode == "numeric":
            left = finite_float(record.output)
            right = finite_float(reference)
            difference = abs(left - right) if left is not None and right is not None else None
            passed = difference is not None and difference <= request.tolerance
            detail: Any = {"absoluteDifference": difference}
        elif request.comparison_mode == "json":
            left_value = record.output
            right_value = reference
            if isinstance(left_value, str):
                try:
                    left_value = json.loads(left_value)
                except json.JSONDecodeError:
                    pass
            if isinstance(right_value, str):
                try:
                    right_value = json.loads(right_value)
                except json.JSONDecodeError:
                    pass
            passed = canonical_json(left_value) == canonical_json(right_value)
            detail = None
        else:
            passed = normalized_text(record.output) == normalized_text(reference)
            detail = None
        comparisons.append({
            "language": record.language,
            "runtime": record.runtime,
            "durationMs": record.duration_ms,
            "exitCode": record.exit_code,
            "pass": passed and record.exit_code == 0,
            "detail": detail,
        })
    passed = len(records) > 1 and not missing and all(record["pass"] for record in comparisons)
    return {
        "ok": passed,
        "schema": "sc-workbench-runtime-reproducibility/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "comparisonMode": request.comparison_mode,
        "tolerance": request.tolerance,
        "requiredLanguages": request.required_languages,
        "missingLanguages": missing,
        "reference": reference,
        "comparisons": comparisons,
        "runtimeVersionCoverage": f"{sum(bool(record.runtime) for record in records)}/{len(records)}",
    }


@router.post("/execution/audit")
def audit_execution(request: AuditRequest) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    if request.language not in LANGUAGE_CATALOG:
        findings.append({"severity": "error", "code": "language-not-allowlisted"})
    if request.language == "assembly":
        findings.append({"severity": "warning", "code": "assembly-profile-only"})
    if not request.explicit_consent:
        findings.append({"severity": "error", "code": "explicit-consent-required"})
    if request.source_bytes > 204800:
        findings.append({"severity": "error", "code": "source-limit-exceeded"})
    if request.output_bytes > 262144:
        findings.append({"severity": "error", "code": "output-limit-exceeded"})
    if request.timeout_seconds > 30:
        findings.append({"severity": "warning", "code": "timeout-above-default-boundary"})
    if request.filesystem_mode == "unrestricted":
        findings.append({"severity": "error", "code": "unrestricted-filesystem-rejected"})
    if request.network_access == "required":
        findings.append({"severity": "warning", "code": "network-not-provided-by-runner"})
    if not findings:
        findings.append({"severity": "pass", "code": "within-default-local-boundary"})
    return {
        "ok": not any(finding["severity"] == "error" for finding in findings),
        "schema": "sc-workbench-execution-audit/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "requested": request.model_dump() if hasattr(request, "model_dump") else request.dict(),
        "enforcedBoundary": {
            "loopbackOnly": True,
            "pairingRequired": True,
            "originBoundToken": True,
            "arbitraryShellEndpoint": False,
            "maximumSourceBytes": 204800,
            "maximumOutputBytes": 262144,
            "temporaryWorkingDirectory": True,
        },
        "findings": findings,
    }
