import subprocess
from pathlib import Path


SAFE_COMMANDS = {
    "pytest",
    "python -m pytest",
    "ls",
    "pwd",
}

MAX_STDOUT_CHARS = 4000
MAX_STDERR_CHARS = 2000


def run_command(command: str, repo_root: str = "./sandbox/sample_repo") -> dict:
    """
    Run a command only if it is in the allowlist.

    Args:
        command: Exact command string to run.
        repo_root: Working directory for the command.

    Returns:
        A structured dict containing command output or an error.
    """
    try:
        repo_path = Path(repo_root).resolve()

        if not repo_path.exists():
            return {
                "ok": False,
                "error": "Repository root does not exist.",
                "command": command,
                "repo_root": str(repo_path),
            }

        if command not in SAFE_COMMANDS:
            return {
                "ok": False,
                "error": f"Command not allowed: {command}",
                "allowed_commands": sorted(SAFE_COMMANDS),
            }

        result = subprocess.run(
            command,
            shell=True,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=20,
        )

        stdout = result.stdout[:MAX_STDOUT_CHARS]
        stderr = result.stderr[:MAX_STDERR_CHARS]

        return {
            "ok": True,
            "command": command,
            "repo_root": str(repo_path),
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "truncated_stdout": len(result.stdout) > MAX_STDOUT_CHARS,
            "truncated_stderr": len(result.stderr) > MAX_STDERR_CHARS,
        }

    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "Command timed out.",
            "command": command,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Unexpected error in run_command: {e}",
            "command": command,
        }
