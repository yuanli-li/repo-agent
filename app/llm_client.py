import json
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


def _latest_tool_result(messages: List[Dict[str, Any]]) -> str:
    """
    Find the latest tool result message we injected back into history.
    """
    for msg in reversed(messages):
        content = msg.get("content", "")
        if isinstance(content, str) and content.startswith("TOOL_RESULT_JSON:"):
            return content
    return ""


def _mock_model_response(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    A tiny heuristic mock model so you can test the loop without real API calls.
    This is NOT smart. It's just enough to validate the architecture.
    """
    task = _latest_user_task(messages).lower()
    latest_tool = _latest_tool_result(messages).lower()

    # First step: choose a tool
    if not latest_tool:
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

    # If search found auth.py, read it
    if "search_code" in latest_tool and "auth.py" in latest_tool:
        return {
            "type": "tool_call",
            "name": "read_file",
            "arguments": {
                "path": "auth.py"
            }
        }

    # If we already read a file, summarize
    if "read_file" in latest_tool:
        return {
            "type": "final",
            "content": "I inspected the file and found the relevant repository logic there. Please review the returned snippet above."
        }

    # If we ran tests, summarize
    if "run_command" in latest_tool:
        return {
            "type": "final",
            "content": "I ran the allowed repository command and summarized its result from the tool output."
        }

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
        "Day 3 recommendation: first run with USE_MOCK_LLM=true. "
        "Later, plug your real provider call here.\n\n"
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
