"""
envforge CLI — main command group and subcommands.

Commands:
  envforge diagnose   Collect and display a DiagnosticReport
  envforge verify     Check if a profile is compatible with this system
  envforge fix        Generate a repair script from a saved report
"""
from __future__ import annotations

import json
import sys
import platform
from pathlib import Path

import click
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich import box

from envforge_agent import __version__
from envforge_agent.report import ReportBuilder
from envforge_agent.schemas import DiagnosticReport

console = Console()
err_console = Console(stderr=True, style="bold red")

def check_macos_support():
    if platform.system() == "Darwin":
        err_console.print("[ERROR] EnvForge is not currently supported on macOS.")
        err_console.print("  Hint: This tool is designed for Linux and Windows (WSL) environments.")
        sys.exit(1)
# ── Root command group ─────────────────────────────────────────────────────────

@click.group()
@click.version_option(__version__, prog_name="envforge-agent")
def cli() -> None:
    """EnvForge CLI Diagnostic Agent — inspect your ML environment."""
    check_macos_support()

# ── envforge diagnose ──────────────────────────────────────────────────────────

@cli.command("diagnose")
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Save report to a JSON file instead of printing to stdout.",
)
@click.option(
    "--send", is_flag=True, default=False,
    help="Send the report to the EnvForge API for compatibility analysis.",
)
@click.option(
    "--api-url",
    default="http://localhost:8000",
    show_default=True,
    envvar="ENVFORGE_API_URL",
    help="Base URL of the EnvForge API.",
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False,
    help="Suppress all output except the JSON report.",
)

@click.option(
    "--sarif", is_flag=True, default=False,
    help="Output diagnostics in SARIF 2.1.0 format for CI/CD pipeline integrations.",
)

def diagnose(output: str | None, send: bool, api_url: str, quiet: bool, sarif: bool) -> None:
    """
    Collect a full diagnostic report of this machine's ML environment.

    Detects: OS, CPU, RAM, GPU, CUDA, cuDNN, Python installations.
    Outputs: DiagnosticReport JSON compatible with POST /api/v1/diagnose.
    """
    if not quiet:
        console.print(Panel(
            f"[bold cyan]EnvForge Diagnostic Agent[/] v{__version__}\n"
            "[dim]Scanning your environment...[/]",
            expand=False,
        ))

    report = ReportBuilder().build()

    if not quiet:
        _print_report_summary(report)

# ── SARIF output ────────────────────────────────────────────────────────
    if sarif:
        import json as _json
        click.echo(_json.dumps(report.to_sarif(), indent=2))
        return
    
    report_json = report.to_json(indent=2)

    # ── Output to file ──────────────────────────────────────────────────────
    if output:
        Path(output).write_text(report_json, encoding="utf-8")
        if not quiet:
            console.print(f"\n[green]✓[/] Report saved to [bold]{output}[/]")
    elif not send:
        # Print JSON to stdout (pipe-friendly)
        click.echo(report_json)

    # ── Send to API ─────────────────────────────────────────────────────────
    if send:
        _send_report(report, api_url, quiet)


def _print_report_summary(report: DiagnosticReport) -> None:
    """Print a human-readable summary table to the terminal."""
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    table.add_column("Category", style="bold cyan", width=14)
    table.add_column("Value")

    table.add_row("OS", f"{report.os.name} {report.os.version} ({report.os.architecture})")
    if report.os.wsl_version:
        table.add_row("WSL", report.os.wsl_version)

    table.add_row("CPU", f"{report.cpu.brand} — {report.cpu.cores}C / {report.cpu.threads}T")
    table.add_row("RAM", f"{report.ram.total_gb} GB total, {report.ram.available_gb} GB free")

    if report.gpus:
        for gpu in report.gpus:
            vram = f"{gpu.vram_gb} GB" if gpu.vram_gb else "?"
            driver = gpu.driver_version or "?"
            table.add_row("GPU", f"{gpu.name} ({vram} VRAM, driver {driver})")
    else:
        table.add_row("GPU", "[dim]No NVIDIA GPU detected[/]")

    if report.cuda.version:
        cudnn = f", cuDNN {report.cuda.cudnn_version}" if report.cuda.cudnn_version else ""
        table.add_row("CUDA", f"{report.cuda.version}{cudnn}")
        if report.cuda.toolkit_path:
            table.add_row("CUDA Path", report.cuda.toolkit_path)
    else:
        table.add_row("CUDA", "[dim]Not detected[/]")

    if report.rocm.version:
        gcn = f" (GCN {report.rocm.gcn_arch})" if report.rocm.gcn_arch else ""
        table.add_row("ROCm", f"{report.rocm.version}{gcn}")
    else:
        table.add_row("ROCm", "[dim]Not detected[/]")

    if report.active_python:
        py = report.active_python
        venv = " [dim](venv)[/]" if py.is_venv else ""
        table.add_row("Python", f"{py.version} at {py.path}{venv}")

    if len(report.python_installations) > 1:
        others = [p for p in report.python_installations
                  if p.path != (report.active_python.path if report.active_python else "")]
        if others:
            table.add_row(
                "Other Pythons",
                ", ".join(f"{p.version} ({p.path})" for p in others[:3]),
            )

    console.print(table)


def _send_report(report: DiagnosticReport, api_url: str, quiet: bool) -> None:
    """POST the DiagnosticReport to the EnvForge API."""
    url = f"{api_url.rstrip('/')}/api/v1/diagnose"
    if not quiet:
        console.print(f"\n[bold]Sending report to[/] {url} ...")

    try:
        response = httpx.post(
            url,
            content=report.to_json(),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        if not quiet:
            _print_diagnose_response(result)
        else:
            click.echo(json.dumps(result, indent=2))

    except httpx.ConnectError:
        err_console.print(f"[ERROR] Cannot connect to {url}")
        err_console.print("  Hint: Is the EnvForge API running? Check ENVFORGE_API_URL.")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        err_console.print(f"[ERROR] API returned {e.response.status_code}")
        err_console.print(e.response.text)
        sys.exit(1)


def _print_diagnose_response(result: dict) -> None:
    """Pretty-print the API diagnose response."""
    console.print("\n[bold green]✓ Compatibility Analysis[/]")

    if result.get("compatible_profiles"):
        console.print(f"  Compatible profiles: {', '.join(result['compatible_profiles'])}")

    if result.get("recommendations"):
        console.print("\n[bold]Recommendations:[/]")
        for rec in result["recommendations"]:
            console.print(f"  • {rec}")

    if result.get("issues"):
        console.print("\n[bold yellow]Issues:[/]")
        for issue in result["issues"]:
            sev = issue.get("severity", "INFO")
            color = {"ERROR": "red", "WARNING": "yellow", "INFO": "cyan"}.get(sev, "white")
            console.print(f"  [{color}][{sev}][/] {issue['message']}")
            if issue.get("suggested_fix"):
                console.print(f"    Fix: {issue['suggested_fix']}")

    console.print(f"\n  Report ID: {result.get('report_id', '?')}")


# ── envforge verify ────────────────────────────────────────────────────────────

@cli.command("verify")
@click.option(
    "--profile", "-p", required=True,
    help="Profile slug to verify against (e.g. pytorch-cuda).",
)
@click.option(
    "--api-url",
    default="http://localhost:8000",
    show_default=True,
    envvar="ENVFORGE_API_URL",
)
def verify(profile: str, api_url: str) -> None:
    """
    Check if this system is compatible with a specific EnvForge profile.

    Collects a DiagnosticReport and sends it to the API for analysis
    against the requested profile.
    """
    console.print(f"[bold cyan]Verifying compatibility with profile:[/] {profile}")
    report = ReportBuilder().build()

    url = f"{api_url.rstrip('/')}/api/v1/diagnose"
    try:
        response = httpx.post(
            url,
            content=report.to_json(),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        compatible = profile in result.get("compatible_profiles", [])
        if compatible:
            console.print(f"[bold green]✓ COMPATIBLE[/] — {profile} is compatible with this system.")
        else:
            console.print(f"[bold red]✗ NOT COMPATIBLE[/] — {profile} is not compatible.")

        if result.get("issues"):
            console.print("\n[bold yellow]Issues:[/]")
            for issue in result["issues"]:
                console.print(f"  • {issue['message']}")
                if issue.get("suggested_fix"):
                    console.print(f"    → {issue['suggested_fix']}")

    except httpx.ConnectError:
        err_console.print(f"Cannot connect to {url}. Is the API running?")
        sys.exit(1)


# ── envforge fix ───────────────────────────────────────────────────────────────

@cli.command("fix")
@click.option(
    "--report", "-r",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
    help="Path to a saved DiagnosticReport JSON file.",
)
@click.option(
    "--profile", "-p",
    required=True,
    help="Profile slug to generate a repair script for.",
)
@click.option(
    "--api-url",
    default="http://localhost:8000",
    show_default=True,
    envvar="ENVFORGE_API_URL",
)
def fix(report: str, profile: str, api_url: str) -> None:
    """
    Generate a repair script based on a saved diagnostic report.

    Sends the report to the API and requests a setup script for the target profile.
    """
    console.print(f"[bold cyan]Generating repair script[/] for profile: {profile}")

    try:
        raw = Path(report).read_text(encoding="utf-8")
        parsed = DiagnosticReport.model_validate_json(raw)
    except Exception as e:
        err_console.print(f"Failed to parse report file: {e}")
        sys.exit(1)

    # Detect OS and Python from the loaded report to build a generate request
    target_os = _map_os_to_target(parsed)
    python_version = _extract_python_version(parsed)

    url = f"{api_url.rstrip('/')}/api/v1/scripts/generate"
    payload = {
        "profile_id": profile,
        "target_os": target_os,
        "python_version": python_version,
        "cuda_version": parsed.cuda.version,
        "output_formats": ["setup.sh"] if target_os != "WIN" else ["setup.ps1", "requirements.txt"],
    }

    try:
        response = httpx.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        console.print(f"[green]✓[/] Scripts generated (job: {result.get('job_id', '?')})")
        for script in result.get("scripts", []):
            console.print(
                Panel(
                    Syntax(script["content"], "bash", theme="monokai", line_numbers=True),
                    title=f"[bold]{script['filename']}[/]",
                )
            )

        download_url = f"{api_url.rstrip('/')}{result.get('download_url', '')}"
        console.print(f"\n  Download all: [link={download_url}]{download_url}[/link]")

    except httpx.ConnectError:
        err_console.print(f"Cannot connect to {url}. Is the API running?")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        err_console.print(f"API error {e.response.status_code}: {e.response.text}")
        sys.exit(1)


def _map_os_to_target(report: DiagnosticReport) -> str:
    if report.os.wsl_version:
        return "WSL"
    if "windows" in report.os.name.lower():
        return "WIN"
    return "LINUX"


def _extract_python_version(report: DiagnosticReport) -> str:
    if report.active_python:
        parts = report.active_python.version.split(".")
        return f"{parts[0]}.{parts[1]}"
    return "3.11"  # safe default
