"""Regression tests for reconstructed v10.11 packages."""

from copy import deepcopy

from app.v10100 import CalculationRequest
from app.v10110 import (
    PackageBuildRequest,
    PackageVerifyRequest,
    build_package,
    verify_package,
)


def sample_package():
    return build_package(
        PackageBuildRequest(
            calculation=CalculationRequest(
                operation="exact",
                expression="2 + 2",
            )
        )
    )


def verify(package, mode="replay"):
    return verify_package(
        PackageVerifyRequest(package=package, mode=mode)
    )


def test_replay_succeeds():
    package = sample_package()
    assert verify(package)["ok"] is True


def test_identical_packages_have_identical_hashes():
    first = sample_package()
    second = sample_package()

    assert first["packageHash"] == second["packageHash"]
    assert (
        first["manifest"]["manifestHash"]
        == second["manifest"]["manifestHash"]
    )


def test_modified_calculation_rejected():
    package = deepcopy(sample_package())
    package["calculation"]["expression"] = "2 + 3"
    assert verify(package)["ok"] is False


def test_modified_result_rejected():
    package = deepcopy(sample_package())
    package["result"]["result"]["exact"] = "5"
    assert verify(package)["ok"] is False


def test_modified_manifest_rejected():
    package = deepcopy(sample_package())
    package["manifest"]["calculationHash"] = "tampered"
    assert verify(package)["ok"] is False


def test_modified_package_hash_rejected():
    package = deepcopy(sample_package())
    package["packageHash"] = "invalid"
    assert verify(package)["ok"] is False


def test_integrity_mode_succeeds():
    assert verify(sample_package(), "integrity")["ok"] is True


def test_integrity_mode_rejects_tampering():
    package = deepcopy(sample_package())
    package["result"]["result"]["exact"] = "999"
    assert verify(package, "integrity")["ok"] is False
