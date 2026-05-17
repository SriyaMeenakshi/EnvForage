from dataclasses import dataclass
from app.templates.engine import TemplateRenderer
from app.templates.models import TemplateContext
from app.compatibility.models import ResolvedEnvironment, ResolvedPackage


def make_context(
    profile_name="myenv",
    python_version="3.10",
    cuda_version=None,
    packages=None,
):
    if packages is None:
        packages = []
    resolved = ResolvedEnvironment(
        python_version=python_version,
        cuda_version=cuda_version,
        target_os="LINUX",
        packages=packages,
    )
    return TemplateContext(
        profile_id="test-id",
        profile_name=profile_name,
        resolved=resolved,
    )


def test_conda_template_renders_basic():
    context = make_context(
        profile_name="myenv",
        python_version="3.10",
        packages=[
            ResolvedPackage(name="numpy", version="1.24.0", cuda_variant=None),
            ResolvedPackage(name="pandas", version="2.0.0", cuda_variant=None),
        ],
    )
    renderer = TemplateRenderer()
    result = renderer.render("environment.yml", context)
    assert "myenv" in result.content
    assert "3.10" in result.content
    assert "numpy" in result.content
    assert "pandas" in result.content


def test_conda_template_no_cuda():
    context = make_context(
        profile_name="cpu-env",
        python_version="3.9",
        cuda_version=None,
        packages=[
            ResolvedPackage(name="scipy", version="1.10.0", cuda_variant=None),
        ],
    )
    renderer = TemplateRenderer()
    result = renderer.render("environment.yml", context)
    assert "cpu-env" in result.content
    assert "scipy" in result.content


def test_conda_template_with_cuda():
    context = make_context(
        profile_name="gpu-env",
        python_version="3.11",
        cuda_version="11.8",
        packages=[
            ResolvedPackage(name="torch", version="2.0.0", cuda_variant="cu118"),
        ],
    )
    renderer = TemplateRenderer()
    result = renderer.render("environment.yml", context)
    assert "gpu-env" in result.content
    assert "3.11" in result.content
    assert "torch" in result.content

