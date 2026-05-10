from app.tools.read_file import read_file
from app.tools.search_code import search_code
from app.tools.run_command import run_command


TOOLS = {
    "read_file": read_file,
    "search_code": search_code,
    "run_command": run_command,
}


def get_tool_schemas() -> list[dict]:
    """
    Return lightweight tool metadata for future LLM/tool-use integration.
    Week 2 先只做最小版，后面可以再扩成更完整的 JSON schema.
    """
    return [
        {
            "name": "read_file",
            "description": "Read a file from the repository by relative path and optional line range.",
            "arguments": {
                "path": "str, required, relative file path inside repo",
                "start_line": "int, optional, default=1",
                "end_line": "int, optional, default=200",
            },
        },
        {
            "name": "search_code",
            "description": "Search code in the repository using a keyword or pattern.",
            "arguments": {
                "query": "str, required, keyword or pattern to search",
            },
        },
        {
            "name": "run_command",
            "description": "Run a safe allowlisted shell command inside the repository.",
            "arguments": {
                "command": "str, required, one of the allowlisted commands",
            },
        },
    ]


def execute_tool(name: str, arguments: dict) -> dict:
    """
    Execute a tool by name.

    Args:
        name: Tool name.
        arguments: Dict of keyword arguments.

    Returns:
        Tool result as a dict.
    """
    if name not in TOOLS:
        return {
            "ok": False,
            "error": f"Unknown tool: {name}",
            "available_tools": sorted(TOOLS.keys()),
        }

    try:
        return TOOLS[name](**arguments)
    except TypeError as e:
        return {
            "ok": False,
            "error": f"Tool argument error for {name}: {e}",
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Unexpected tool execution error for {name}: {e}",
        }
