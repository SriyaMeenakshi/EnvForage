"""
ROCm Compatibility Matrix.

Maps ROCm versions to minimum required driver versions and supported GPUs.

Sources:
  - AMD ROCm Release Notes: https://rocm.docs.amd.com/en/latest/release/release-notes.html
  - PyTorch ROCm Support: https://pytorch.org/get-started/locally/
"""
from app.compatibility.models import ROCMMatrixEntry

# ── ROCm Version → Driver + GPU Matrix ───────────────────────────────────────

ROCM_MATRIX: dict[str, ROCMMatrixEntry] = {
    "5.4.2": ROCMMatrixEntry(
        rocm_version="5.4.2",
        min_driver_linux="5.19",
        supported_gpus=["gfx906", "gfx908", "gfx90a", "gfx1030"],
        notes="Stable release for RHEL 8/9 and Ubuntu 20.04/22.04.",
    ),
    "5.6.0": ROCMMatrixEntry(
        rocm_version="5.6.0",
        min_driver_linux="5.19",
        supported_gpus=["gfx906", "gfx908", "gfx90a", "gfx1030", "gfx1100"],
        notes="Added support for Instinct MI300 and Radeon 7000 series.",
    ),
    "5.7.0": ROCMMatrixEntry(
        rocm_version="5.7.0",
        min_driver_linux="6.2",
        supported_gpus=["gfx906", "gfx908", "gfx90a", "gfx1030", "gfx1100", "gfx1101"],
        notes="Improved PyTorch integration.",
    ),
    "6.0.0": ROCMMatrixEntry(
        rocm_version="6.0.0",
        min_driver_linux="6.5",
        supported_gpus=["gfx906", "gfx908", "gfx90a", "gfx940", "gfx1030", "gfx1100"],
        notes="Latest stable. Significant performance boost for LLMs.",
    ),
}

SUPPORTED_ROCM_VERSIONS: list[str] = sorted(ROCM_MATRIX.keys())

# ── Framework → ROCm Support Map ─────────────────────────────────────────────

FRAMEWORK_ROCM_SUPPORT: dict[str, dict[str, list[str]]] = {
    "torch": {
        "2.0.0": ["5.4.2"],
        "2.1.0": ["5.4.2", "5.6.0"],
        "2.2.0": ["5.6.0", "5.7.0"],
        "2.3.0": ["5.7.0", "6.0.0"],
        "2.4.0": ["6.0.0"],
    },
    "tensorflow": {
        "2.13.0": ["5.4.2"],
        "2.14.0": ["5.6.0"],
    },
}


def get_rocm_entry(rocm_version: str) -> ROCMMatrixEntry | None:
    """Return ROCm matrix entry for the given version, or None if not found."""
    return ROCM_MATRIX.get(rocm_version)


def get_supported_rocm_for_framework(framework: str, version: str) -> list[str]:
    """Return list of supported ROCm versions for a given framework version."""
    return FRAMEWORK_ROCM_SUPPORT.get(framework, {}).get(version, [])
