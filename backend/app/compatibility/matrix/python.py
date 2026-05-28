"""
Python Version Compatibility Matrix.

Maps ML framework versions to their supported Python version ranges.
Data is now dynamically generated and loaded from python_matrix_data.json.

Sources:
  - PyPI Metadata (Requires-Python) for Python version constraints.
  - PyTorch: https://pytorch.org/get-started/locally/
  - TensorFlow: https://www.tensorflow.org/install/pip#software_requirements
  - Ultralytics YOLOv8: https://docs.ultralytics.com/quickstart/
"""
import json
from pathlib import Path

from app.compatibility.models import FrameworkVersionEntry

# ── Framework Version → Python Compatibility ──────────────────────────────────

MATRIX_JSON_PATH = Path(__file__).resolve().parent / "python_matrix_data.json"

with open(MATRIX_JSON_PATH) as f:
    _raw_data = json.load(f)

PYTHON_MATRIX: dict[str, list[FrameworkVersionEntry]] = {}
for _framework, _entries in _raw_data.items():
    PYTHON_MATRIX[_framework] = [FrameworkVersionEntry(**kwargs) for kwargs in _entries]


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
