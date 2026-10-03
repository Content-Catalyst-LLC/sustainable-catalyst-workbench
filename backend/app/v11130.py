"""Workbench v11.13.0 — Number Theory & Discrete Mathematics.

Adds exact integer arithmetic, modular arithmetic, prime/factorization tools,
combinatorics, recurrences, finite sequences, and basic graph-theoretic
operations to the unified v11 CalculationObject.
"""
from __future__ import annotations

from collections import deque
from math import gcd
from typing import Any, Dict, List, Literal, Optional

import sympy as sp
from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-number-theory-discrete-mathematics-status/1.0"
RESULT_SCHEMA = "sc-workbench-number-theory-discrete-result/1.0"

router = APIRouter(tags=["workbench-v11130-number-theory-discrete-mathematics"])


class DiscreteMathRequest(BaseModel):
    operation: Literal[
        "gcd-lcm",
        "extended-gcd",
        "prime-test",
        "factor-integer",
        "totient",
        "mobius",
        "divisors",
        "modular-inverse",
        "modular-power",
        "crt",
        "permutations-combinations",
        "binomial",
        "sequence",
        "recurrence-solve",
        "graph-properties",
        "graph-shortest-path",
        "graph-connected-components",
    ]
    a: Optional[int] = None
    b: Optional[int] = None
    n: Optional[int] = None
    k: Optional[int] = None
    exponent: Optional[int] = None
    modulus: Optional[int] = None
    residues: List[int] = Field(default_factory=list, max_length=1000)
    moduli: List[int] = Field(default_factory=list, max_length=1000)
    sequenceType: Optional[Literal["fibonacci", "lucas", "primes", "squares", "triangular"]] = None
    count: int = Field(default=10, ge=1, le=10000)
    recurrence: Optional[str] = Field(default=None, max_length=5000)
    functionName: str = Field(default="a", max_length=100)
    initialConditions: Dict[int, int] = Field(default_factory=dict)
    nodes: List[str] = Field(default_factory=list, max_length=10000)
    edges: List[List[str]] = Field(default_factory=list, max_length=50000)
    directed: bool = False
    source: Optional[str] = None
    target: Optional[str] = None


class DiscreteCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    discreteMath: DiscreteMathRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _require(value, name: str):
    if value is None:
        raise ValueError(f"{name} is required")
    return value


def _graph(req: DiscreteMathRequest):
    nodes = set(req.nodes)
    adjacency: Dict[str, set[str]] = {n: set() for n in nodes}
    for edge in req.edges:
        if len(edge) != 2:
            raise ValueError("each edge must contain exactly two node ids")
        u, v = str(edge[0]), str(edge[1])
        nodes.update([u, v])
        adjacency.setdefault(u, set()).add(v)
        adjacency.setdefault(v, set())
        if not req.directed:
            adjacency[v].add(u)
    return sorted(nodes), adjacency


def _components(nodes, adjacency, directed=False):
    # For directed graphs this returns weakly connected components.
    undirected = {n: set(adjacency.get(n, set())) for n in nodes}
    if directed:
        for u in nodes:
            for v in adjacency.get(u, set()):
                undirected.setdefault(v, set()).add(u)
    seen = set()
    comps = []
    for start in nodes:
        if start in seen:
            continue
        q = [start]
        seen.add(start)
        comp = []
        while q:
            u = q.pop()
            comp.append(u)
            for v in undirected.get(u, set()):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        comps.append(sorted(comp))
    return comps


def execute_discrete_math(req: DiscreteMathRequest) -> Dict[str, Any]:
    op = req.operation
    verification: Dict[str, Any] = {}
    details: Dict[str, Any] = {}
    method = op

    if op == "gcd-lcm":
        a, b = int(_require(req.a, "a")), int(_require(req.b, "b"))
        g = gcd(a, b)
        l = 0 if a == 0 or b == 0 else abs(a * b) // g
        result: Any = {"gcd": g, "lcm": l}
        verification["productIdentity"] = (a == 0 or b == 0) or abs(a*b) == g*l

    elif op == "extended-gcd":
        a, b = int(_require(req.a, "a")), int(_require(req.b, "b"))
        g, x, y = sp.gcdex(a, b)
        # SymPy gcdex returns (s, t, h).
        s, t, h = int(g), int(x), int(y)
        result = {"x": s, "y": t, "gcd": h}
        verification["bezoutIdentity"] = a*s + b*t == h
        method = "sympy-gcdex"

    elif op == "prime-test":
        n = int(_require(req.n, "n"))
        result = {"n": n, "isPrime": bool(sp.isprime(n))}
        method = "sympy-isprime"

    elif op == "factor-integer":
        n = int(_require(req.n, "n"))
        factors = sp.factorint(n)
        result = {"n": n, "factors": {str(k): int(v) for k, v in factors.items()}}
        reconstructed = 1
        for p, e in factors.items():
            reconstructed *= int(p) ** int(e)
        verification["reconstructsInput"] = reconstructed == n
        method = "sympy-factorint"

    elif op == "totient":
        n = int(_require(req.n, "n"))
        result = {"n": n, "totient": int(sp.totient(n))}
        method = "sympy-totient"

    elif op == "mobius":
        n = int(_require(req.n, "n"))
        result = {"n": n, "mobius": int(sp.mobius(n))}
        method = "sympy-mobius"

    elif op == "divisors":
        n = int(_require(req.n, "n"))
        ds = [int(x) for x in sp.divisors(n)]
        result = {"n": n, "divisors": ds, "count": len(ds)}
        verification["allDivideN"] = all(n % d == 0 for d in ds)
        method = "sympy-divisors"

    elif op == "modular-inverse":
        a = int(_require(req.a, "a"))
        m = int(_require(req.modulus, "modulus"))
        inv = int(sp.mod_inverse(a, m))
        result = {"inverse": inv, "modulus": m}
        verification["multiplicativeIdentity"] = (a * inv) % m == 1
        method = "sympy-mod-inverse"

    elif op == "modular-power":
        a = int(_require(req.a, "a"))
        e = int(_require(req.exponent, "exponent"))
        m = int(_require(req.modulus, "modulus"))
        value = pow(a, e, m)
        result = {"value": value, "modulus": m}
        verification["rangeValid"] = 0 <= value < abs(m)
        method = "python-pow-modular"

    elif op == "crt":
        if not req.residues or not req.moduli or len(req.residues) != len(req.moduli):
            raise ValueError("crt requires equal-length residues and moduli")
        from sympy.ntheory.modular import crt
        solved = crt(req.moduli, req.residues)
        if solved is None:
            result = {"solvable": False, "solution": None}
            verification["satisfiesCongruences"] = False
        else:
            value, modulus = map(int, solved)
            result = {"solvable": True, "solution": value, "modulus": modulus}
            verification["satisfiesCongruences"] = all(
                value % int(m) == int(r) % int(m)
                for r, m in zip(req.residues, req.moduli)
            )
        method = "sympy-chinese-remainder-theorem"

    elif op == "permutations-combinations":
        n = int(_require(req.n, "n"))
        k = int(_require(req.k, "k"))
        if n < 0 or k < 0 or k > n:
            raise ValueError("require 0 <= k <= n")
        result = {
            "n": n, "k": k,
            "permutations": int(sp.factorial(n) / sp.factorial(n-k)),
            "combinations": int(sp.binomial(n, k)),
        }
        verification["combinationSymmetry"] = int(sp.binomial(n,k)) == int(sp.binomial(n,n-k))

    elif op == "binomial":
        n = int(_require(req.n, "n"))
        k = int(_require(req.k, "k"))
        result = {"value": int(sp.binomial(n, k))}
        method = "sympy-binomial"

    elif op == "sequence":
        typ = _require(req.sequenceType, "sequenceType")
        c = int(req.count)
        if typ == "fibonacci":
            values = [int(sp.fibonacci(i)) for i in range(c)]
        elif typ == "lucas":
            values = [int(sp.lucas(i)) for i in range(c)]
        elif typ == "primes":
            values = [int(sp.prime(i+1)) for i in range(c)]
        elif typ == "squares":
            values = [i*i for i in range(c)]
        elif typ == "triangular":
            values = [i*(i+1)//2 for i in range(c)]
        else:
            raise ValueError(f"unsupported sequenceType: {typ}")
        result = {"sequenceType": typ, "values": values, "count": c}
        method = "exact-finite-sequence"

    elif op == "recurrence-solve":
        if not req.recurrence:
            raise ValueError("recurrence-solve requires recurrence")
        n = sp.symbols("n", integer=True)
        f = sp.Function(req.functionName)
        locals_map = {"n": n, req.functionName: f}
        eq = sp.sympify(req.recurrence, locals=locals_map)
        if not isinstance(eq, sp.Equality):
            raise ValueError("recurrence must be an equation, e.g. Eq(a(n), a(n-1)+a(n-2))")
        ics = {f(int(k)): sp.Integer(v) for k, v in req.initialConditions.items()}
        solution = sp.rsolve(eq.lhs - eq.rhs, f(n), init=ics if ics else None)
        result = {"closedForm": None if solution is None else str(solution)}
        verification["solutionFound"] = solution is not None
        method = "sympy-rsolve"

    elif op == "graph-properties":
        nodes, adjacency = _graph(req)
        edge_count = len(req.edges)
        degrees = {}
        if req.directed:
            indegree = {n: 0 for n in nodes}
            outdegree = {n: len(adjacency.get(n, set())) for n in nodes}
            for u in nodes:
                for v in adjacency.get(u, set()):
                    indegree[v] += 1
            degrees = {"inDegree": indegree, "outDegree": outdegree}
        else:
            degrees = {"degree": {n: len(adjacency.get(n, set())) for n in nodes}}
        comps = _components(nodes, adjacency, req.directed)
        result = {
            "nodeCount": len(nodes),
            "edgeCount": edge_count,
            "degrees": degrees,
            "connectedComponents": comps,
            "connected": len(comps) <= 1,
        }
        verification["handshakeLemma"] = (
            True if req.directed
            else sum(degrees["degree"].values()) == 2 * edge_count
        )
        method = "deterministic-adjacency-graph-analysis"

    elif op == "graph-shortest-path":
        nodes, adjacency = _graph(req)
        source = _require(req.source, "source")
        target = _require(req.target, "target")
        if source not in adjacency or target not in adjacency:
            raise ValueError("source and target must exist in graph")
        q = deque([source])
        prev = {source: None}
        while q:
            u = q.popleft()
            if u == target:
                break
            for v in sorted(adjacency.get(u, set())):
                if v not in prev:
                    prev[v] = u
                    q.append(v)
        if target not in prev:
            result = {"path": None, "distanceEdges": None, "reachable": False}
        else:
            path = []
            cur = target
            while cur is not None:
                path.append(cur)
                cur = prev[cur]
            path.reverse()
            result = {"path": path, "distanceEdges": len(path)-1, "reachable": True}
        verification["pathEndpointsValid"] = (
            not result["reachable"] or (result["path"][0] == source and result["path"][-1] == target)
        )
        method = "breadth-first-search"

    elif op == "graph-connected-components":
        nodes, adjacency = _graph(req)
        comps = _components(nodes, adjacency, req.directed)
        result = {"components": comps, "count": len(comps)}
        verification["coversAllNodes"] = sorted(x for c in comps for x in c) == sorted(nodes)
        method = "deterministic-component-search"

    else:
        raise ValueError(f"Unsupported discrete mathematics operation: {op}")

    body = {
        "ok": True,
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": "sympy-exact-discrete",
        "runtime": "python",
        "method": method,
        "result": result,
        "details": details,
        "verification": verification,
        "wordpressRequired": False,
    }
    body["resultHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok","resultHash"}}
    )
    return body


def calculation_object_extension(req: UnifiedCalculationRequest, discrete_req: DiscreteMathRequest):
    obj = build_calculation_object(req)
    result = execute_discrete_math(discrete_req)
    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["discreteMath"] = result
    obj["result"]["discreteMath"] = result["result"]
    obj["executionPlan"]["discreteMath"] = {
        "runtime": "python",
        "engine": "sympy-exact-discrete",
        "operation": discrete_req.operation,
        "method": result["method"],
    }
    obj["verification"]["discreteMath"] = result["verification"]
    obj["provenance"]["discreteMathResultHash"] = result["resultHash"]
    obj["calculationObjectHash"] = _hash(
        {k:v for k,v in obj.items() if k not in {"ok","calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Number Theory & Discrete Mathematics",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "sympy-exact-discrete",
        "wordpressRequired": False,
        "capabilities": {
            "gcdLcm": True,
            "extendedEuclideanAlgorithm": True,
            "primeTesting": True,
            "integerFactorization": True,
            "totientMobiusDivisors": True,
            "modularInversePower": True,
            "chineseRemainderTheorem": True,
            "permutationsCombinations": True,
            "binomialCoefficients": True,
            "finiteSequences": True,
            "recurrenceSolving": True,
            "graphProperties": True,
            "shortestPathBfs": True,
            "connectedComponents": True,
            "exactDiscreteVerification": True,
            "calculationObjectExtension": True,
        },
    }


@router.get("/v11130/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/discrete-math")
def discrete_math_route(req: DiscreteMathRequest):
    return execute_discrete_math(req)


@router.post("/calculation-engine/v1/discrete-math/calculation-object")
def discrete_math_calculation_object_route(req: DiscreteCalculationObjectRequest):
    return calculation_object_extension(req.calculationObjectRequest, req.discreteMath)
