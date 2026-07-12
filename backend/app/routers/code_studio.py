from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/code-studio", tags=["code-studio"])


@router.get("/manifest")
def code_studio_manifest() -> dict:
    """Describe the v1.9.1 editor-first browser runtimes and future local-runner contract.

    This endpoint is descriptive only. User programs execute in browser
    workers on the visitor device; FastAPI does not accept executable source.
    """
    return {
        "ok": True,
        "version": "1.9.1",
        "phase": "editor-first-browser-runtime-pack",
        "execution_enabled": True,
        "execution_location": "visitor-browser",
        "storage": {
            "primary": "indexeddb",
            "fallback": "localstorage",
            "scope": "browser-origin",
            "project_upload_default": False,
        },
        "limits": {
            "execution_timeout_ms": 15000,
            "max_source_bytes": 262144,
            "max_table_rows_rendered": 500,
            "network_access": "restricted",
        },
        "browser_runtimes": [
            {
                "id": "javascript",
                "status": "available",
                "target": "dedicated-worker",
                "version": "browser-es",
                "release": "1.9.1",
            },
            {
                "id": "python",
                "status": "available",
                "target": "pyodide-worker",
                "version": "Pyodide 314.0.2",
                "release": "1.9.1",
            },
            {
                "id": "r",
                "status": "available",
                "target": "webr",
                "version": "webR 0.6.0 / R 4.6.0",
                "release": "1.9.1",
            },
            {
                "id": "sql",
                "status": "available",
                "target": "duckdb-wasm",
                "version": "DuckDB-Wasm 1.30.0",
                "release": "1.9.1",
            },
        ],
        "runner_contract": {
            "implementation": "go",
            "release": "2.0.0",
            "transport": "loopback-structured-jobs",
            "loopback_only": True,
            "pairing_required": True,
            "arbitrary_shell": False,
            "status": "draft",
        },
        "safety": {
            "fastapi_executes_user_code": False,
            "wordpress_executes_user_code": False,
            "project_files_uploaded_by_default": False,
            "browser_runtime_network_restricted": True,
        },
    }
