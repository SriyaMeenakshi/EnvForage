import sys
import json
import urllib.request
from typing import Optional

def fetch_pypi_python_requires(package: str, version: Optional[str] = None) -> None:
    """
    Fetches the Requires-Python metadata from PyPI for a given package and version.
    This script is used to automate the verification of Python compatibility matrices.
    """
    url = f"https://pypi.org/pypi/{package}/json"
    if version:
        url = f"https://pypi.org/pypi/{package}/{version}/json"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'EnvForage/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            info = data.get("info", {})
            pkg_version = info.get("version", "unknown")
            requires_python = info.get("requires_python", "Not specified")
            
            print(f"Package: {package}")
            print(f"Version: {pkg_version}")
            print(f"Requires-Python: {requires_python}")
            
    except urllib.error.HTTPError as e:
        print(f"Failed to fetch metadata for {package} {version or ''}: HTTP {e.code}")
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_pypi_metadata.py <package_name> [version]")
        sys.exit(1)
        
    pkg = sys.argv[1]
    ver = sys.argv[2] if len(sys.argv) > 2 else None
    fetch_pypi_python_requires(pkg, ver)
