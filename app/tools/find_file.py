from pathlib import Path


def find_file(pattern, repo_root):
    matches = []
    MAX_MATCHES = 20
    match_count = 0

    # --- 防守式校验开始 ---
    # 1. 首先判断是否为 None 或非字符串类型
    if pattern is None or not isinstance(pattern, str):
        return {
            "ok": False,
            "pattern": pattern,
            "error": "Pattern must be a non-null string.",
            "matches": [],
            "match_count": 0,
            "truncated": False
        }

    # 2. 现在可以安全地进行 strip 了
    pattern = pattern.strip()

    # 3. 判断 strip 之后是否为空字符串
    if not pattern:
        return {
            "ok": False,
            "pattern": pattern,
            "error": "Pattern cannot be empty or just whitespace.",
            "matches": [],
            "match_count": 0,
            "truncated": False
        }
    # --- 防守式校验结束 ---

    # 路径校验
    try:
        abs_repo_root = Path(repo_root).resolve()
    except Exception as e:
        return {
            "ok": False,
            "pattern": pattern,
            "error": f"Path resolution failed: {str(e)}",
            "matches": [],
            "match_count": 0,
            "truncated": False
        }

    if not (abs_repo_root.exists() and abs_repo_root.is_dir()):
        return {
            "ok": False,
            "pattern": pattern,
            "error": "Invalid repo_root.",
            "matches": [],
            "match_count": 0,
            "truncated": False
        }

    IGNORED_DIRS = {".pytest_cache", ".git",
                    "__pycache__", ".venv", "venv", "dist", "build"}

    for path_obj in abs_repo_root.rglob("*"):
        if not path_obj.is_file():
            continue

        rel_path_obj = path_obj.relative_to(abs_repo_root)

        if any(part in IGNORED_DIRS for part in rel_path_obj.parts):
            continue

        pattern_cf = pattern.casefold()
        rel_path = str(rel_path_obj)
        if pattern_cf in rel_path.casefold():
            matches.append(rel_path)
            match_count += 1

    return {
        "ok": True,
        "pattern": pattern,
        "error": None,
        "matches": sorted(matches)[:MAX_MATCHES],
        "match_count": match_count,
        "truncated": match_count > MAX_MATCHES
    }
