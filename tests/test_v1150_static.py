from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity_v1150():
    release=(ROOT/"backend/app/release.py").read_text()
    main=(ROOT/"backend/app/main.py").read_text()
    plugin=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert 'APP_VERSION = "11.5.0"' in release
    assert 'version="11.5.0"' in main
    assert "from app.v1150 import router as v1150_router" in main
    assert "app.include_router(v1150_router)" in main
    assert "Version: 11.5.0" in plugin
    assert "SCWB_VERSION', '11.5.0" in plugin

def test_julia_routes_and_runner_exist():
    p=(ROOT/"backend/app/v1150.py").read_text()
    assert "/calculation-engine/v1/runtimes/julia/execute" in p
    assert "/calculation-engine/v1/runtimes/julia/calculation-object" in p
    assert "arbitraryCodeExecution" in p
    assert (ROOT/"backend/julia-runtime/runner.jl").exists()

def test_unified_planner_marks_julia_active():
    p=(ROOT/"backend/app/v1100.py").read_text()
    assert 'selected = "julia"' in p
    assert '"enabled": True' in p
    assert '"julia": "active-scientific"' in p
    assert '"activeRuntimes": ["python", "julia"]' in p

def test_dockerfile_carries_julia():
    p=(ROOT/"backend/Dockerfile").read_text()
    assert "FROM julia:1.11-bookworm AS julia_runtime" in p
    assert "COPY --from=julia_runtime /usr/local/julia /usr/local/julia" in p
    assert 'ENV PATH="/usr/local/julia/bin:${PATH}"' in p

def test_wordpress_adapter_proxy_only():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1150-julia-scientific-runtime.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/runtimes/julia" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_compose_current_release():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.5.0" in c
    assert "d.get('version')=='11.5.0'" in c
