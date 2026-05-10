from pathlib import Path


def read_file(
    path: str,
    start_line: int = 1,
    end_line: int = 200,
    repo_root: str = "./sandbox/sample_repo",
) -> dict:
    """
    Read a file inside the repository, with basic path safety checks.

    Args:
        path: Relative path inside the repository.
        start_line: 1-based inclusive start line.
        end_line: 1-based inclusive end line.
        repo_root: Root directory of the repository.

    Returns:
        A structured dict containing file content or an error.
    """
    try:
        repo_path = Path(repo_root).resolve()
        file_path = (repo_path / path).resolve()

        # Prevent path traversal outside the repo root
        if not str(file_path).startswith(str(repo_path)):
            return {
                "ok": False,
                "error": "Access denied: file is outside repo root.",
                "path": path,
            }

        if not file_path.exists():
            return {
                "ok": False,
                "error": "File not found.",
                "path": path,
            }

        if not file_path.is_file():
            return {
                "ok": False,
                "error": "Path is not a file.",
                "path": path,
            }

        # Normalize line range
        if start_line < 1:
            start_line = 1
        if end_line < start_line:
            end_line = start_line

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        total_lines = len(lines)
        start_idx = start_line - 1
        end_idx = min(end_line, total_lines)

        snippet_lines = []
        for i in range(start_idx, end_idx):
            snippet_lines.append(f"{i + 1}: {lines[i]}")

        return {
            "ok": True,
            "path": path,
            "absolute_path": str(file_path),
            "start_line": start_line,
            "end_line": end_idx,
            "total_lines": total_lines,
            "content": "\n".join(snippet_lines),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": f"Unexpected error in read_file: {e}",
            "path": path,
        }
