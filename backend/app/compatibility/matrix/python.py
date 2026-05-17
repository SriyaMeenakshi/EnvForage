"""
Python Version Compatibility Matrix.

Maps ML framework versions to their supported Python version ranges.

Sources:
  - PyTorch: https://pytorch.org/get-started/locally/ (Python support column)
  - TensorFlow: https://www.tensorflow.org/install/pip#software_requirements
  - Ultralytics YOLOv8: https://docs.ultralytics.com/quickstart/
  - Diffusers: https://huggingface.co/docs/diffusers/installation

TODO: Automate this from PyPI metadata in a future phase.
"""
from app.compatibility.models import FrameworkVersionEntry

# ── Framework Version → Python Compatibility ──────────────────────────────────

PYTHON_MATRIX: dict[str, list[FrameworkVersionEntry]] = {
    "torch": [
        FrameworkVersionEntry(
            framework="torch", version="2.0.0",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.7", "11.8"],
        ),
        FrameworkVersionEntry(
            framework="torch", version="2.0.1",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.7", "11.8"],
        ),
        FrameworkVersionEntry(
            framework="torch", version="2.1.0",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.8", "12.1"],
        ),
        FrameworkVersionEntry(
            framework="torch", version="2.1.1",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.8", "12.1"],
        ),
        FrameworkVersionEntry(
            framework="torch", version="2.1.2",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.8", "12.1"],
            supported_rocm=["5.4.2", "5.6.0"],
        ),
        FrameworkVersionEntry(
            framework="torch", version="2.2.0",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.8", "12.1"],
        ),
        FrameworkVersionEntry(
            framework="torch", version="2.2.1",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.8", "12.1"],
        ),
        FrameworkVersionEntry(
            framework="torch", version="2.2.2",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.8", "12.1"],
        ),
        FrameworkVersionEntry(
            framework="torch", version="2.3.0",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.8", "12.1"],
        ),
        FrameworkVersionEntry(
            framework="torch", version="2.4.0",
            min_python="3.8", max_python="3.12",
            supported_python=["3.8", "3.9", "3.10", "3.11", "3.12"],
            supported_cuda=["11.8", "12.1", "12.4"],
            supported_rocm=["6.0.0"],
        ),
    ],
    "tensorflow": [
        # Note: TensorFlow on Windows requires WSL2 for GPU support (TF 2.11+)
        FrameworkVersionEntry(
            framework="tensorflow", version="2.13.0",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.8"],
        ),
        FrameworkVersionEntry(
            framework="tensorflow", version="2.14.0",
            min_python="3.9", max_python="3.11",
            supported_python=["3.9", "3.10", "3.11"],
            supported_cuda=["11.8"],
        ),
        FrameworkVersionEntry(
            framework="tensorflow", version="2.15.0",
            min_python="3.9", max_python="3.11",
            supported_python=["3.9", "3.10", "3.11"],
            supported_cuda=["12.1"],
        ),
        # TODO: Add TF 2.16+ once officially released with stable CUDA mapping
    ],
    "ultralytics": [
        FrameworkVersionEntry(
            framework="ultralytics", version="8.0.0",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.8", "12.1"],
        ),
        FrameworkVersionEntry(
            framework="ultralytics", version="8.1.0",
            min_python="3.8", max_python="3.11",
            supported_python=["3.8", "3.9", "3.10", "3.11"],
            supported_cuda=["11.8", "12.1"],
        ),
        FrameworkVersionEntry(
            framework="ultralytics", version="8.2.0",
            min_python="3.8", max_python="3.12",
            supported_python=["3.8", "3.9", "3.10", "3.11", "3.12"],
            supported_cuda=["11.8", "12.1", "12.4"],
        ),
    ],
}


def get_framework_versions(framework: str) -> list[FrameworkVersionEntry]:
    """Return all known versions for a framework."""
    return PYTHON_MATRIX.get(framework, [])


def get_framework_entry(framework: str, version: str) -> FrameworkVersionEntry | None:
    """Return the matrix entry for a specific framework version."""
    for entry in PYTHON_MATRIX.get(framework, []):
        if entry.version == version:
            return entry
    return None


def get_latest_compatible_version(
    framework: str,
    python_version: str,
    cuda_version: str | None = None,
    rocm_version: str | None = None,
) -> str | None:
    """
    Return the latest framework version compatible with the given
    Python, CUDA, and ROCm versions. Returns None if no compatible version found.
    """
    candidates = []
    for entry in PYTHON_MATRIX.get(framework, []):
        if python_version not in entry.supported_python:
            continue
        if cuda_version is not None and cuda_version not in entry.supported_cuda:
            continue
        if rocm_version is not None and rocm_version not in entry.supported_rocm:
            continue
        candidates.append(entry.version)

    if not candidates:
        return None

    # Sort descending by version tuple and return the first (latest)
    candidates.sort(key=lambda v: tuple(int(x) for x in v.split(".")), reverse=True)
    return candidates[0]
