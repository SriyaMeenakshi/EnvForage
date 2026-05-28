import json
import os
import sys
from pathlib import Path

# Add backend to path so we can import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from packaging.specifiers import SpecifierSet
from app.compatibility.matrix.python import PYTHON_MATRIX
from app.compatibility.models import FrameworkVersionEntry

MATRIX_JSON_PATH = Path(__file__).resolve().parent.parent / "app" / "compatibility" / "matrix" / "python_matrix_data.json"
SUPPORTED_PYTHONS = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]

def fetch_pypi_python_bounds(package: str, version: str):
    """Fetch required python bounds from PyPI."""
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    print(f"Fetching {url}...")
    r = httpx.get(url)
    
    if r.status_code != 200:
        print(f"  [WARN] Failed to fetch {package} {version} (Status {r.status_code})")
        return None

    data = r.json()
    requires_python = data.get("info", {}).get("requires_python")
    
    if not requires_python:
        print(f"  [WARN] No requires_python found for {package} {version}")
        return None

    try:
        spec = SpecifierSet(requires_python)
    except Exception as e:
        print(f"  [WARN] Failed to parse specifier '{requires_python}': {e}")
        return None
        
    supported = []
    for py_ver in SUPPORTED_PYTHONS:
        # Check against x.y.0
        if spec.contains(f"{py_ver}.0"):
            supported.append(py_ver)
            
    if not supported:
        return None
        
    return {
        "min_python": supported[0],
        "max_python": supported[-1],
        "supported_python": supported
    }

def main():
    print("Automating PyPI metadata retrieval for PYTHON_MATRIX...")
    
    # Check if JSON already exists; if so, load from it to allow continuous updates.
    # Otherwise, bootstrap from the currently imported PYTHON_MATRIX.
    if MATRIX_JSON_PATH.exists():
        print(f"Loading existing data from {MATRIX_JSON_PATH.name}")
        with open(MATRIX_JSON_PATH, "r") as f:
            raw_data = json.load(f)
    else:
        print("Bootstrapping from hardcoded python.py...")
        from dataclasses import asdict
        raw_data = {fw: [asdict(entry) for entry in entries] for fw, entries in PYTHON_MATRIX.items()}

    updated_data = {}
    
    for framework, entries in raw_data.items():
        updated_data[framework] = []
        for entry in entries:
            version = entry["version"]
            bounds = fetch_pypi_python_bounds(framework, version)
            
            if bounds:
                entry["min_python"] = bounds["min_python"]
                entry["max_python"] = bounds["max_python"]
                entry["supported_python"] = bounds["supported_python"]
                print(f"  Updated {framework} {version}: {bounds['supported_python']}")
            else:
                print(f"  Kept original bounds for {framework} {version}")
                
            updated_data[framework].append(entry)
            
    print(f"\nWriting updated matrix to {MATRIX_JSON_PATH.name}...")
    with open(MATRIX_JSON_PATH, "w") as f:
        json.dump(updated_data, f, indent=4)
        
    print("Done! You can now configure python.py to load from this JSON file.")

if __name__ == "__main__":
    main()
