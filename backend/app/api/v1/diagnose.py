"""Diagnose endpoint — POST /api/v1/diagnose."""
import uuid
from datetime import datetime

from fastapi import APIRouter

from app.api.deps import DB
from app.models.diagnostic import DiagnosticReport
from app.schemas.diagnostic import CompatibilityIssue, DiagnoseResponse, DiagnosticReportSchema

router = APIRouter()


@router.post("/diagnose", response_model=DiagnoseResponse, status_code=201)
async def diagnose(
    report: DiagnosticReportSchema,
    db: DB,
) -> DiagnoseResponse:
    """
    Accept a DiagnosticReport from the CLI agent and return
    a compatibility analysis: which profiles are compatible,
    and what issues were found.
    """
    # Persist the raw report
    db_report = DiagnosticReport(
        id=uuid.uuid4(),
        report_data=report.model_dump(),
        os_type=report.os.name.split()[0].upper()[:5] if report.os else None,
        gpu_name=report.gpus[0].name if report.gpus else None,
        cuda_version=report.cuda.version if report.cuda else None,
        rocm_version=report.rocm.version if report.rocm else None,
        python_version=report.active_python.version[:4] if report.active_python else None,
        driver_version=report.gpus[0].driver_version if report.gpus else None,
        created_at=datetime.utcnow(),
    )
    db.add(db_report)
    await db.flush()

    # TODO: Phase 2 — Run full compatibility analysis against all profiles
    # For Phase 1, return a basic analysis based on CUDA version
    issues: list[CompatibilityIssue] = []
    compatible_profiles: list[str] = []
    recommendations: list[str] = []

    cuda_ver = report.cuda.version if report.cuda else None

    if cuda_ver:
        from app.compatibility.matrix.cuda import CUDA_MATRIX
        if cuda_ver not in CUDA_MATRIX:
            issues.append(CompatibilityIssue(
                severity="WARNING",
                component="cuda",
                message=f"CUDA {cuda_ver} is not in EnvForge's validated matrix.",
                suggested_fix=f"Supported CUDA versions: {', '.join(CUDA_MATRIX.keys())}",
                docs_url="https://docs.nvidia.com/cuda/",
            ))
        else:
            compatible_profiles.extend(["pytorch-cuda", "yolov8", "stable-diffusion", "llm-finetune"])
            recommendations.append(f"pytorch-cuda with CUDA {cuda_ver}")
    elif report.rocm.version:
        rocm_ver = report.rocm.version
        from app.compatibility.matrix.rocm import ROCM_MATRIX
        if rocm_ver not in ROCM_MATRIX:
            issues.append(CompatibilityIssue(
                severity="WARNING",
                component="rocm",
                message=f"ROCm {rocm_ver} is not in EnvForge's validated matrix.",
                suggested_fix=f"Supported ROCm versions: {', '.join(ROCM_MATRIX.keys())}",
                docs_url="https://rocm.docs.amd.com/en/latest/",
            ))
        else:
            compatible_profiles.extend(["pytorch-rocm", "yolov8"])
            recommendations.append(f"pytorch-rocm with ROCm {rocm_ver}")
    else:
        compatible_profiles.extend(["opencv-beginner", "yolov8"])
        recommendations.append("opencv-beginner (CPU-only, no CUDA or ROCm detected)")

    return DiagnoseResponse(
        report_id=str(db_report.id),
        compatible_profiles=compatible_profiles,
        issues=issues,
        recommendations=recommendations,
    )
