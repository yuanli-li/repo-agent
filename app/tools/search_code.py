import subprocess
from pathlib import Path


MAX_STDOUT_CHARS = 4000
MAX_STDERR_CHARS = 1000


def search_code(query: str, repo_root: str = "./sandbox/sample_repo") -> dict:
    """
    Search the repository using ripgrep.

    Args:
        query: Search keyword or pattern.
        repo_root: Root directory of the repository.

    Returns:
        A structured dict containing rg output or an error.
    """
    try:
        repo_path = Path(repo_root).resolve()

        if not repo_path.exists():
            return {
                "ok": False,
                "error": "Repository root does not exist.",
                "query": query,
                "repo_root": str(repo_path),
            }

        if not query or not query.strip():
            return {
                "ok": False,
                "error": "Search query is empty.",
                "query": query,
            }

        # -n => line numbers
        # --hidden can be added later if needed, but avoid for now
        cmd = ["rg", "-n", query, str(repo_path)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )

        stdout = result.stdout[:MAX_STDOUT_CHARS]
        stderr = result.stderr[:MAX_STDERR_CHARS]

        return {
            "ok": True,
            "query": query,
            "repo_root": str(repo_path),
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "truncated_stdout": len(result.stdout) > MAX_STDOUT_CHARS,
            "truncated_stderr": len(result.stderr) > MAX_STDERR_CHARS,
        }

    except FileNotFoundError:
        return {
            "ok": False,
            "error": "ripgrep (rg) is not installed. Please install it first.",
            "query": query,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "Search timed out.",
            "query": query,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Unexpected error in search_code: {e}",
            "query": query,
        }
