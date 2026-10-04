from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "12.9.0"' in (ROOT/"backend/app/release.py").read_text()
    m = (ROOT/"backend/app/main.py").read_text()
    assert 'version="12.9.0"' in m
    assert "from app.v1290 import router as v1290_router" in m
    assert "app.include_router(v1290_router)" in m

def test_migration_contract():
    p = (ROOT/"backend/app/v1290.py").read_text()
    assert "/standalone/v1/migration/certification" in p
    assert "/standalone/v1/migration/capability-matrix" in p
    assert "/standalone/v1/migration/runbook" in p
    assert "wordpressRemovalDoesNotChangeV12CanonicalContracts" in p
    assert '"12.10.0"' in p

def test_standalone_client():
    p = (ROOT/"standalone-client/migration-certification.js").read_text()
    assert "StandaloneMigrationCertificationClient" in p
    assert "capabilityMatrix" in p
    assert "runbook" in p
    assert "sessionProbe" in p

def test_standalone_app():
    p = (ROOT/"standalone-app/app-shell.js").read_text()
    assert "loadMigrationCertification" in p
    assert "MIGRATION CERTIFIED" in p
    assert "migrationCertification" in p

def test_wordpress_adapter_is_compatibility_only():
    p = (ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1290-standalone-migration-certification.php").read_text()
    assert "wordpressRequired = false" in p
    assert "compatibility/status adapter only" in p
    for term in [
        "update_option(",
        "update_user_meta(",
        "set_transient(",
        "wp_insert_post(",
    ]:
        assert term not in p

def test_compose_identity():
    c = (ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.9.0" in c
    assert "d.get('version')=='12.9.0'" in c
