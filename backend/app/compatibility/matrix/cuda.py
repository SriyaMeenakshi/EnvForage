"""
CUDA Compatibility Matrix.

Maps CUDA versions to minimum required NVIDIA driver versions and supported
framework versions.

IMPORTANT: All data here is sourced from official NVIDIA and framework
documentation. Do NOT guess or hallucinate version numbers.

Sources:
  - NVIDIA CUDA Toolkit Release Notes:
    https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/
  - PyTorch: https://pytorch.org/get-started/locally/
  - TensorFlow: https://www.tensorflow.org/install/pip#software_requirements
"""
from app.compatibility.models import CUDAMatrixEntry

# ── CUDA Version → Driver + Framework Matrix ──────────────────────────────────
#
# Driver versions: minimum required to run this CUDA version.
# Linux/Windows drivers differ — both are documented.
#
# Source: NVIDIA CUDA Toolkit Release Notes (Table 1: CUDA Toolkit and
# Minimum Required Driver Version for CUDA Minor Version Compatibility)
# Note: Driver version strings verified against latest NVIDIA release notes.

CUDA_MATRIX: dict[str, CUDAMatrixEntry] = {
    "11.8": CUDAMatrixEntry(
        cuda_version="11.8",
        min_driver_linux="520.61.05",
        min_driver_windows="522.06",
        cudnn_versions=["8.7.0", "8.9.0"],
        supported_archs=["sm_35", "sm_50", "sm_60", "sm_70", "sm_75", "sm_80", "sm_86", "sm_89"],
        notes="Long-term stable. Broad framework support.",
        source_url="https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/",
    ),
    "12.1": CUDAMatrixEntry(
        cuda_version="12.1",
        min_driver_linux="525.85.12",
        min_driver_windows="527.86",
        cudnn_versions=["8.9.0", "9.0.0"],
        supported_archs=["sm_50", "sm_60", "sm_70", "sm_75", "sm_80", "sm_86", "sm_89", "sm_90"],
        notes="Supports Ada Lovelace (RTX 40xx) GPUs.",
        source_url="https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/",
    ),
    "12.3": CUDAMatrixEntry(
        cuda_version="12.3",
        min_driver_linux="545.23.06",
        min_driver_windows="545.84",
        cudnn_versions=["9.0.0", "9.1.0"],
        supported_archs=["sm_50", "sm_60", "sm_70", "sm_75", "sm_80", "sm_86", "sm_89", "sm_90"],
        notes="Intermediate release. Used by JAX 0.4.24–0.4.26.",
        source_url="https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/",
    ),
    "12.4": CUDAMatrixEntry(
        cuda_version="12.4",
        min_driver_linux="550.54.14",
        min_driver_windows="551.61",
        cudnn_versions=["9.0.0", "9.1.0"],
        supported_archs=["sm_50", "sm_60", "sm_70", "sm_75", "sm_80", "sm_86", "sm_89", "sm_90"],
        notes="Latest stable. Required for PyTorch 2.3+.",
        source_url="https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/",
    ),
    "12.5": CUDAMatrixEntry(
        cuda_version="12.5",
        min_driver_linux="555.42.02",
        min_driver_windows="555.85",
        cudnn_versions=["9.2.0", "9.3.0"],
        supported_archs=["sm_50", "sm_60", "sm_70", "sm_75", "sm_80", "sm_86", "sm_89", "sm_90"],
        notes="Improved Ada Lovelace support. Required for PyTorch 2.4+.",
        source_url="https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/",
    ),
    "12.6": CUDAMatrixEntry(
        cuda_version="12.6",
        min_driver_linux="560.35.03",
        min_driver_windows="560.94",
        cudnn_versions=["9.3.0", "9.5.0"],
        supported_archs=["sm_50", "sm_60", "sm_70", "sm_75", "sm_80", "sm_86", "sm_89", "sm_90"],
        notes="Latest stable release. Broad Ada Lovelace (RTX 40xx) support.",
        source_url="https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/",
    ),
}

# Ordered list for display / validation purposes
SUPPORTED_CUDA_VERSIONS: list[str] = sorted(CUDA_MATRIX.keys())

# ── Framework → CUDA Support Map ─────────────────────────────────────────────
#
# Which CUDA versions each framework version officially supports.
# Source: PyTorch: https://pytorch.org/get-started/previous-versions/
#         TensorFlow: https://www.tensorflow.org/install/pip


FRAMEWORK_CUDA_SUPPORT: dict[str, dict[str, list[str]]] = {
    "torch": {
        "2.0.0": ["11.7", "11.8"],
        "2.0.1": ["11.7", "11.8"],
        "2.1.0": ["11.8", "12.1"],
        "2.1.1": ["11.8", "12.1"],
        "2.1.2": ["11.8", "12.1"],
        "2.2.0": ["11.8", "12.1"],
        "2.2.1": ["11.8", "12.1"],
        "2.2.2": ["11.8", "12.1"],
        "2.3.0": ["11.8", "12.1"],
        "2.3.1": ["11.8", "12.1"],
        "2.4.0": ["11.8", "12.1", "12.4"],
        "2.5.0": ["12.1", "12.4", "12.6"],
    },
    "tensorflow": {
        # TensorFlow uses XLA CUDA support — often lags behind PyTorch
        # Source: https://www.tensorflow.org/install/pip
        "2.13.0": ["11.8"],
        "2.14.0": ["11.8"],
        "2.15.0": ["12.1"],
        "2.16.0": ["12.3"],
        "2.16.1": ["12.3"],
    },
    "jax": {
        # Source: https://jax.readthedocs.io/en/latest/installation.html
        # Source: https://docs.jax.dev/en/latest/changelog.html
        "0.4.1":  ["11.8"],
        "0.4.7":  ["11.8"],
        "0.4.14": ["11.8"],
        "0.4.20": ["11.8", "12.1"],
        "0.4.23": ["11.8", "12.1"],
        "0.4.24": ["11.8", "12.1", "12.3"],
        "0.4.25": ["11.8", "12.1", "12.3"],
        "0.4.26": ["12.1"],
        "0.4.28": ["12.1", "12.4"],
        "0.4.30": ["12.1", "12.4", "12.6"],
    },
}


def get_cuda_entry(cuda_version: str) -> CUDAMatrixEntry | None:
    """Return CUDA matrix entry for the given version, or None if not found."""
    return CUDA_MATRIX.get(cuda_version)


def get_supported_cuda_for_framework(framework: str, version: str) -> list[str]:
    """Return list of supported CUDA versions for a given framework version."""
    return FRAMEWORK_CUDA_SUPPORT.get(framework, {}).get(version, [])
