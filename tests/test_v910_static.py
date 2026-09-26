from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_release_identity_and_routes():
    assert 'APP_VERSION = "9.12.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'from app.v910 import router as v910_router' in main and 'app.include_router(v910_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.12.0' in compose

def test_protocol_builder_package_surfaces():
    module=(ROOT/'backend/app/v910.py').read_text()
    for path in ('/protocol-builder/manifest','/protocol-builder/compose','/protocol-builder/protocols','/protocol-builder/execution-plan','/integration/core/protocol-builder/plan','/v910/status'): assert path in module
    assert 'automaticSampleSizeCalculation":False' in module and 'automaticExecutionDispatch":False' in module

def test_wordpress_and_deployment_contracts():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); inc=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v910-experimental-design-research-protocol-builder.php'
    assert 'Version: 9.12.0' in main and inc.exists() and 'sc_workbench_research_protocol_builder' in inc.read_text()
    dep=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_1_0_contabo.sh').read_text(); assert 'rsync -a --checksum' in dep and '127.0.0.1:8088' in dep and 'sustainable-catalyst-workbench:9.1.0' in dep
    inst=(ROOT/'installers/apply_and_push_workbench_v9_1_0_macos.sh').read_text(); assert 'rsync -a --checksum' in inst and "APP_VERSION=='9.1.0'" in inst
