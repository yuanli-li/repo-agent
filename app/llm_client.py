import json
import re
from typing import Any, Dict, List

from app.config import settings


def _render_messages_as_text(messages: List[Dict[str, Any]]) -> str:
    """
    Convert message history into a plain text transcript.
    This keeps Day 3 simple and provider-agnostic.
    """
    parts = []
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        parts.append(f"{role}:\n{content}\n")
    return "\n".join(parts)


def _extract_json(raw_text: str) -> Dict[str, Any]:
    """
    Parse a JSON string from model output.
    Day 3 version assumes model follows instructions reasonably well.
    """
    raw_text = raw_text.strip()

    # Remove markdown fences if the model accidentally adds them
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json", "", 1).strip()

    try:
        data = json.loads(raw_text)
        if not isinstance(data, dict):
            raise ValueError("Model output is not a JSON object.")
        return data
    except Exception as e:
        return {
            "type": "final",
            "content": f"[Parse error] Model output was not valid JSON. Raw output: {raw_text[:500]}. Error: {e}"
        }


def _latest_user_task(messages: List[Dict[str, Any]]) -> str:
    for msg in messages:
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def _parse_latest_tool_result(messages: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """
    Parse the most recent TOOL_RESULT_JSON message.
    """
    for msg in reversed(messages):
        content = msg.get("content", "")
        if isinstance(content, str) and content.startswith("TOOL_RESULT_JSON:"):
            raw_json = content.replace("TOOL_RESULT_JSON:", "", 1).strip()
            try:
                return json.loads(raw_json)
            except Exception:
                return None
    return None


def _grounded_final_from_tool_result(
    tool_name: str,
    tool_result: Dict[str, Any],
    user_task: str
) -> Dict[str, Any]:
    """
    Build a grounded final answer from the latest tool result.
    Stronger Day 4 version:
    - code files: summarize functions + logic
    - README/text files: summarize headings + description
    - search results: summarize matches
    - commands: summarize status + key output
    """
    if tool_name == "read_file":
        path = tool_result.get("path", "unknown file")
        content = tool_result.get("content", "")

        lower_path = path.lower()

        if lower_path.endswith(".py"):
            summary = _summarize_python_file(path, content, user_task)
            return {"type": "final", "content": summary}

        if lower_path.endswith(".md") or lower_path.endswith(".txt"):
            summary = _summarize_markdown_or_text_file(
                path, content, user_task)
            return {"type": "final", "content": summary}

        # fallback for other file types
        cleaned = _strip_line_numbers(content)
        lines = _nonempty_lines(cleaned)
        preview = " ".join(lines[:5])[:300]
        return {
            "type": "final",
            "content": f"I read `{path}`. A short preview is: {preview}"
        }

    if tool_name == "search_code":
        summary = _summarize_search_results(tool_result, user_task)
        return {"type": "final", "content": summary}

    if tool_name == "run_command":
        summary = _summarize_command_result(tool_result, user_task)
        return {"type": "final", "content": summary}

    return {
        "type": "final",
        "content": "I completed the last tool step, but I do not yet have a grounded summary for this tool type."
    }


def _mock_model_response(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    A tiny heuristic mock model so you can test the loop without real API calls.
    This is NOT smart. It's just enough to validate the architecture.
    """
    task = _latest_user_task(messages).lower()
    latest_tool_payload = _parse_latest_tool_result(messages)

    # First step: choose a tool
    if latest_tool_payload is None:
        if "readme" in task:
            return {
                "type": "tool_call",
                "name": "read_file",
                "arguments": {
                    "path": "README.md"
                }
            }

        if "test" in task or "pytest" in task:
            return {
                "type": "tool_call",
                "name": "run_command",
                "arguments": {
                    "command": "pytest"
                }
            }

        if "verify_token" in task or "auth" in task or "jwt" in task or "login" in task:
            return {
                "type": "tool_call",
                "name": "search_code",
                "arguments": {
                    "query": "verify_token"
                }
            }

        return {
            "type": "tool_call",
            "name": "search_code",
            "arguments": {
                "query": task[:30] if task else "auth"
            }
        }

    tool_name = latest_tool_payload.get("tool_name", "")
    tool_result = latest_tool_payload.get("result", {})

    # If search found auth.py, read it before finalizing
    if tool_name == "search_code":
        stdout = tool_result.get("stdout", "")
        if "auth.py" in stdout:
            return {
                "type": "tool_call",
                "name": "read_file",
                "arguments": {
                    "path": "auth.py"
                }
            }

        # Otherwise, summarize the search result directly
        return _grounded_final_from_tool_result(tool_name, tool_result, task)

    # If we already read a file, synthesize grounded final answer
    if tool_name == "read_file":
        return _grounded_final_from_tool_result(tool_name, tool_result, task)

    # If we ran a command, synthesize grounded final answer
    if tool_name == "run_command":
        return _grounded_final_from_tool_result(tool_name, tool_result, task)

    return {
        "type": "final",
        "content": "I do not have enough reliable information to continue."
    }


def _call_real_model_as_text(
    messages: List[Dict[str, Any]],
    system_prompt: str,
    tools: List[Dict[str, Any]]
) -> str:
    """
    Placeholder for real provider integration.

    Day 3 recommendation:
    keep this unimplemented, or implement your chosen provider later
    while preserving the same return contract.

    It should return raw text that is a JSON object string.
    """
    transcript = _render_messages_as_text(messages)

    combined_prompt = (
        system_prompt
        + "\n\nAVAILABLE TOOLS:\n"
        + json.dumps(tools, indent=2)
        + "\n\nCONVERSATION:\n"
        + transcript
        + "\n\nReturn exactly one JSON object."
    )

    raise NotImplementedError(
        "Day 4 recommendation: keep USE_MOCK_LLM=true while validating logging "
        "and grounded final synthesis.\n\n"
        f"Prompt preview:\n{combined_prompt[:1000]}"
    )


def call_model(
    messages: List[Dict[str, Any]],
    system_prompt: str,
    tools: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Unified model interface.

    Always returns one of:
    1. {"type": "tool_call", "name": ..., "arguments": {...}}
    2. {"type": "final", "content": "..."}
    """
    if settings.use_mock_llm:
        return _mock_model_response(messages)

    raw_text = _call_real_model_as_text(messages, system_prompt, tools)
    parsed = _extract_json(raw_text)

    if parsed.get("type") == "tool_call":
        if "name" not in parsed or "arguments" not in parsed:
            return {
                "type": "final",
                "content": f"[Invalid tool call schema] {parsed}"
            }
        return parsed

    if parsed.get("type") == "final":
        return {
            "type": "final",
            "content": parsed.get("content", "")
        }

    return {
        "type": "final",
        "content": f"[Invalid response type] {parsed}"
    }


def _strip_line_numbers(text: str) -> str:
    """
    Convert:
        '1: foo\\n2: bar'
    into:
        'foo\\nbar'
    """
    cleaned_lines = []
    for line in text.splitlines():
        cleaned = re.sub(r"^\s*\d+:\s?", "", line)
        cleaned_lines.append(cleaned)
    return "\n".join(cleaned_lines)


def _nonempty_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _extract_python_function_signatures(lines: List[str]) -> List[str]:
    signatures = []
    for line in lines:
        if line.startswith("def "):
            signatures.append(line)
    return signatures[:5]


def _extract_python_class_signatures(lines: List[str]) -> List[str]:
    classes = []
    for line in lines:
        if line.startswith("class "):
            classes.append(line)
    return classes[:5]


def _summarize_python_logic(lines: List[str]) -> List[str]:
    """
    Very lightweight rule-based logic summary.
    Not a real parser, just useful heuristics for small files.
    """
    summaries = []

    joined = "\n".join(lines)

    # Common patterns
    if "if not token" in joined and "return False" in joined:
        summaries.append("it returns `False` when the token is empty")

    if "return token == SECRET_TOKEN" in joined:
        summaries.append(
            "it checks whether the given token matches `SECRET_TOKEN`")

    if "if verify_token(token)" in joined:
        summaries.append(
            "it uses `verify_token(token)` to determine whether login succeeds")

    # Generic if/return pattern hints
    if "return True" in joined and not any("returns `True`" in s for s in summaries):
        summaries.append("it contains a branch that returns `True`")

    if "return False" in joined and not any("returns `False`" in s for s in summaries):
        summaries.append("it contains a branch that returns `False`")

    return summaries[:4]


def _summarize_python_file(path: str, content: str, user_task: str) -> str:
    cleaned = _strip_line_numbers(content)
    lines = _nonempty_lines(cleaned)

    func_sigs = _extract_python_function_signatures(lines)
    class_sigs = _extract_python_class_signatures(lines)
    logic_points = _summarize_python_logic(lines)

    parts = [f"The relevant code is in `{path}`."]

    if func_sigs:
        if len(func_sigs) == 1:
            parts.append(f"The key function is `{func_sigs[0]}`.")
        else:
            joined = "; ".join(f"`{sig}`" for sig in func_sigs[:3])
            parts.append(f"The file defines these functions: {joined}.")

    if class_sigs:
        joined = "; ".join(f"`{sig}`" for sig in class_sigs[:3])
        parts.append(f"It also defines classes such as {joined}.")

    if logic_points:
        logic_text = "; ".join(logic_points)
        parts.append(f"From the code, {logic_text}.")

    # If we still do not have much, include a short cleaned preview
    if not func_sigs and not logic_points:
        preview = " ".join(lines[:5])[:300]
        parts.append(f"A short preview of the file is: {preview}")

    return " ".join(parts)


def _summarize_markdown_or_text_file(path: str, content: str, user_task: str) -> str:
    cleaned = _strip_line_numbers(content)
    lines = _nonempty_lines(cleaned)

    if not lines:
        return f"I read `{path}`, but it appears to be empty."

    headings = [line for line in lines if line.startswith("#")]
    non_heading_lines = [line for line in lines if not line.startswith("#")]

    parts = []

    # Avoid duplicate phrasing for README-specific tasks
    if "readme" in user_task.lower():
        parts.append(f"The README is in `{path}`.")
    else:
        parts.append(f"The file is `{path}`.")

    if headings:
        # Clean markdown heading markers like #, ##, ###
        main_heading = headings[0].lstrip("#").strip()
        if main_heading:
            parts.append(f"The main heading is: {main_heading}.")

    if non_heading_lines:
        preview = " ".join(non_heading_lines[:3])[:350]
        parts.append(f"It describes: {preview}")

    return " ".join(parts)


def _summarize_search_results(tool_result: Dict[str, Any], user_task: str) -> str:
    query = tool_result.get("query", "")
    stdout = tool_result.get("stdout", "")
    lines = [line.strip() for line in stdout.splitlines() if line.strip()][:5]

    if not lines:
        return f"I searched the repository for `{query}`, but did not find any matches."

    return f"I searched the repository for `{query}` and found matches in: " + "; ".join(lines)


def _summarize_command_result(tool_result: Dict[str, Any], user_task: str) -> str:
    command = tool_result.get("command", "")
    returncode = tool_result.get("returncode", "")
    stdout = tool_result.get("stdout", "")

    parts = [f"I ran `{command}`."]

    if returncode == 0:
        parts.append("The command completed successfully.")
    else:
        parts.append(f"The command failed with return code {returncode}.")

    if "pytest" in command:
        m = re.search(r"collected\s+(\d+)\s+items", stdout)
        passed = re.search(r"(\d+)\s+passed", stdout)

        if m and passed:
            parts.append(
                f"Pytest collected {m.group(1)} tests and all {passed.group(1)} passed.")
        else:
            preview = " ".join(_nonempty_lines(stdout)[:4])[:300]
            parts.append(f"Pytest output preview: {preview}")
    else:
        preview = " ".join(_nonempty_lines(stdout)[:4])[:300]
        if preview:
            parts.append(f"Output preview: {preview}")

    return " ".join(parts)
