"""AI Layer — Pydantic models for structured troubleshoot requests and responses."""
from typing import Any, Literal
from pydantic import BaseModel, Field


# ── Request Models ────────────────────────────────────────────────────────────

class TroubleshootRequest(BaseModel):
    """
    Structured input for the AI troubleshoot endpoint.

    The ``diagnostic`` field contains the raw DiagnosticReport dict (as received
    from the CLI agent or the frontend diagnostic dashboard). It is kept as a
    dict to avoid circular imports with the diagnostic schemas module.
    """
    diagnostic: dict[str, Any] = Field(
        ..., description="Raw DiagnosticReport JSON from the CLI agent or frontend."
    )
    profile_slug: str | None = Field(
        None, description="Target profile slug (e.g. 'pytorch-cuda')."
    )
    profile_name: str | None = Field(
        None, description="Human-readable profile name."
    )
    target_os: str | None = Field(
        None, description="Target OS: LINUX, WSL, or WIN."
    )
    python_version: str | None = Field(
        None, description="Requested Python version (e.g. '3.11')."
    )
    cuda_version: str | None = Field(
        None, description="Requested CUDA version (e.g. '12.1')."
    )
    user_description: str = Field(
        "", description="Free-text description of the issue from the user.",
        max_length=500,
    )
    session_id: str | None = Field(
        None, description="Optional previous session ID to continue a conversation."
    )


# ── Response Models ───────────────────────────────────────────────────────────

class SuggestedFix(BaseModel):
    step: int
    title: str
    description: str
    severity: Literal["CRITICAL", "WARNING", "INFO"]
    safe_commands: list[str] = Field(default_factory=list)
    repair_template_id: str | None = None


class TroubleshootResponse(BaseModel):
    session_id: str
    root_cause: str
    suggested_fixes: list[SuggestedFix]
    repair_script_available: bool = False
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    disclaimer: str = (
        "AI suggestions are advisory only. Review all steps before executing. "
        "EnvForge is not responsible for system changes."
    )


# ── Metadata ──────────────────────────────────────────────────────────────────

class LLMResponseMeta(BaseModel):
    """Metadata about the LLM call, used for audit logging."""
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

