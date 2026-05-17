"""
Unit tests for the Compatibility Resolver.
No mocks for matrix data — the matrix IS the ground truth.
"""
import pytest
from app.compatibility.errors import IncompatibilityError, UnsupportedOSError, UnknownVersionError
from app.compatibility.models import PackageConstraint
from app.compatibility.resolver import CompatibilityResolver

R = CompatibilityResolver()

def test_resolve_pytorch_cuda118_py311():
    result = R.resolve(
        packages=[PackageConstraint("torch", "2.1.2")],
        python_version="3.11", cuda_version="11.8", target_os="LINUX",
        profile_slug="pytorch-cuda", os_support=["LINUX", "WSL"], cuda_required=True,
    )
    assert result.packages[0].version == "2.1.2"
    assert result.packages[0].cuda_variant == "cu118"

def test_resolve_cpu_only():
    result = R.resolve(
        packages=[PackageConstraint("opencv-python", "4.9.0.80")],
        python_version="3.11", cuda_version=None, target_os="WIN",
        profile_slug="opencv-beginner", os_support=["LINUX", "WSL", "WIN"], cuda_required=False,
    )
    assert result.cuda_version is None
    assert result.packages[0].cuda_variant is None

def test_wsl_note_in_warnings():
    result = R.resolve(
        packages=[PackageConstraint("torch", "2.1.0")],
        python_version="3.10", cuda_version="11.8", target_os="WSL",
        profile_slug="pytorch-cuda", os_support=["LINUX", "WSL"], cuda_required=True,
    )
    assert any("WSL" in w for w in result.warnings)

def test_version_override():
    result = R.resolve(
        packages=[PackageConstraint("torch", "2.1.2")],
        python_version="3.11", cuda_version="11.8", target_os="LINUX",
        profile_slug="pytorch-cuda", os_support=["LINUX", "WSL"], cuda_required=True,
        overrides={"torch": "2.2.2"},
    )
    assert result.packages[0].version == "2.2.2"

def test_unsupported_os_raises():
    with pytest.raises(UnsupportedOSError) as exc:
        R.resolve(
            packages=[PackageConstraint("torch", "2.1.0")],
            python_version="3.11", cuda_version="11.8", target_os="WIN",
            profile_slug="pytorch-cuda", os_support=["LINUX", "WSL"], cuda_required=True,
        )
    assert exc.value.requested_os == "WIN"

def test_unknown_cuda_raises():
    with pytest.raises(UnknownVersionError) as exc:
        R.resolve(
            packages=[PackageConstraint("torch", "2.1.0")],
            python_version="3.11", cuda_version="10.2", target_os="LINUX",
            profile_slug="pytorch-cuda", os_support=["LINUX", "WSL"], cuda_required=True,
        )
    assert exc.value.version == "10.2"

def test_python_mismatch_raises():
    with pytest.raises(IncompatibilityError) as exc:
        R.resolve(
            packages=[PackageConstraint("torch", "2.1.0")],
            python_version="3.7", cuda_version="11.8", target_os="LINUX",
            profile_slug="pytorch-cuda", os_support=["LINUX", "WSL"], cuda_required=True,
        )
    assert exc.value.component == "python"

def test_cuda_required_without_version_raises():
    with pytest.raises(IncompatibilityError) as exc:
        R.resolve(
            packages=[PackageConstraint("torch", "2.1.0")],
            python_version="3.11", cuda_version=None, target_os="LINUX",
            profile_slug="pytorch-cuda", os_support=["LINUX", "WSL"], cuda_required=True,
        )
    assert exc.value.component == "cuda"

def test_cuda_version_mismatch_raises():
    with pytest.raises(IncompatibilityError) as exc:
        R.resolve(
            packages=[PackageConstraint("torch", "2.1.0")],
            python_version="3.11", cuda_version="12.4", target_os="LINUX",
            profile_slug="pytorch-cuda", os_support=["LINUX", "WSL"], cuda_required=True,
        )
    assert exc.value.component == "cuda"

def test_non_matrix_package_uses_spec():
    result = R.resolve(
        packages=[PackageConstraint("matplotlib", "3.8.4")],
        python_version="3.11", cuda_version=None, target_os="LINUX",
        profile_slug="opencv-beginner", os_support=["LINUX", "WIN", "WSL"], cuda_required=False,
    )
    assert result.packages[0].version == "3.8.4"

def test_to_dict_serializes():
    result = R.resolve(
        packages=[PackageConstraint("torch", "2.1.0")],
        python_version="3.11", cuda_version="11.8", target_os="LINUX",
        profile_slug="pytorch-cuda", os_support=["LINUX", "WSL"], cuda_required=True,
    )
    d = result.to_dict()
    assert d["python_version"] == "3.11"
    assert isinstance(d["packages"], list)


# ── JAX CUDA Support Matrix Tests ─────────────────────────────────────────────

def test_jax_cuda118_supported():
    """JAX 0.4.14 supports only CUDA 11.8."""
    from app.compatibility.matrix.cuda import get_supported_cuda_for_framework
    cuda_versions = get_supported_cuda_for_framework("jax", "0.4.14")
    assert set(cuda_versions) == {"11.8"}

def test_jax_cuda121_supported():
    """JAX 0.4.28 supports CUDA 12.1 and 12.4."""
    from app.compatibility.matrix.cuda import get_supported_cuda_for_framework
    cuda_versions = get_supported_cuda_for_framework("jax", "0.4.28")
    assert set(cuda_versions) == {"12.1", "12.4"}

def test_jax_cuda124_supported():
    """JAX 0.4.28 supports CUDA 12.1 and 12.4."""
    from app.compatibility.matrix.cuda import get_supported_cuda_for_framework
    cuda_versions = get_supported_cuda_for_framework("jax", "0.4.28")
    assert set(cuda_versions) == {"12.1", "12.4"}

def test_jax_cuda118_dropped_in_0426():
    """JAX 0.4.26 supports only CUDA 12.1, not 11.8."""
    from app.compatibility.matrix.cuda import get_supported_cuda_for_framework
    cuda_versions = get_supported_cuda_for_framework("jax", "0.4.26")
    assert set(cuda_versions) == {"12.1"}

def test_jax_unknown_version_returns_empty():
    """Unknown JAX version should return empty list, not crash."""
    from app.compatibility.matrix.cuda import get_supported_cuda_for_framework
    cuda_versions = get_supported_cuda_for_framework("jax", "0.0.0")
    assert cuda_versions == []
