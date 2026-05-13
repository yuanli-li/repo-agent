import json
from typing import Any, Dict, List

from app.config import settings
from app.prompts import SYSTEM_PROMPT
from app.tool_registry import execute_tool, get_tool_schemas
from app.logger import StepLogger
from app.llm_client import (
    call_model,
    should_programmatic_finalize,
    build_programmatic_final,
)


class RepoAgent:
    def __init__(self, repo_root: str, max_steps: int = 6):
        self.repo_root = repo_root
        self.max_steps = max_steps
        self.tools = get_tool_schemas()
        self.logger = StepLogger(log_dir="logs")

    def _make_initial_messages(self, user_task: str) -> List[Dict[str, Any]]:
        return [
            {
                "role": "user",
                "content": user_task
            }
        ]

    def _append_tool_result(
        self,
        messages: List[Dict[str, Any]],
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
    ) -> None:
        """
        Add both:
        1. what the assistant tried to do
        2. what the tool actually returned

        Day 3 version uses plain-text messages with stable prefixes.
        """
        messages.append(
            {
                "role": "assistant",
                "content": "TOOL_CALL_JSON: " + json.dumps(
                    {
                        "name": tool_name,
                        "arguments": tool_args
                    },
                    ensure_ascii=False
                )
            }
        )

        messages.append(
            {
                "role": "user",
                "content": "TOOL_RESULT_JSON: " + json.dumps(
                    {
                        "tool_name": tool_name,
                        "result": tool_result
                    },
                    ensure_ascii=False
                )
            }
        )

    def _summarize_tool_result(self, tool_name: str, tool_result: Dict[str, Any]) -> str:
        """
        Produce a short summary for logs.
        """
        if not isinstance(tool_result, dict):
            return str(tool_result)[:300]

        if tool_name == "read_file":
            path = tool_result.get("path", "")
            content = tool_result.get("content", "")
            return f"read_file path={path}, content_preview={content[:200]}"

        if tool_name == "search_code":
            query = tool_result.get("query", "")
            stdout = tool_result.get("stdout", "")
            lines = stdout.splitlines()[:5]
            return f"search_code query={query}, matches={lines}"

        if tool_name == "run_command":
            command = tool_result.get("command", "")
            returncode = tool_result.get("returncode", "")
            stdout = tool_result.get("stdout", "")
            return f"run_command command={command}, returncode={returncode}, stdout_preview={stdout[:200]}"

        return str(tool_result)[:300]

    def run(self, user_task: str) -> str:
        messages = self._make_initial_messages(user_task)

        print("\n=== AGENT START ===")
        print("Task:", user_task)
        print("Log file:", self.logger.get_log_path())

        self.logger.log_event(
            "agent_start",
            {
                "user_task": user_task,
                "repo_root": self.repo_root,
                "max_steps": self.max_steps,
            }
        )

        for step in range(1, self.max_steps + 1):
            print(f"\n--- Step {step} ---")

            decision = call_model(
                messages=messages,
                system_prompt=SYSTEM_PROMPT,
                tools=self.tools
            )

            print("Model decision:", decision)

            # Log the decision first
            self.logger.log_step({
                "event_type": "model_decision",
                "step_id": step,
                "user_task": user_task,
                "decision": decision,
                "message_count": len(messages),
            })

            if decision["type"] == "final":
                final_answer = decision["content"]
                messages.append(
                    {
                        "role": "assistant",
                        "content": final_answer
                    }
                )

                self.logger.log_step({
                    "event_type": "agent_stop",
                    "step_id": step,
                    "stop_reason": "final_answer",
                    "final_answer": final_answer,
                    "message_count": len(messages),
                })
                print("\n=== AGENT FINAL ===")
                print(final_answer)
                return final_answer

            if decision["type"] == "tool_call":
                tool_name = decision["name"]
                tool_args = dict(decision["arguments"])

                if "repo_root" not in tool_args:
                    tool_args["repo_root"] = self.repo_root

                tool_result = execute_tool(tool_name, tool_args)

                print("Executing tool:", tool_name)
                print("Tool args:", tool_args)
                print("Tool result:", tool_result)

                tool_result_summary = self._summarize_tool_result(
                    tool_name, tool_result)

                self.logger.log_step({
                    "event_type": "tool_execution",
                    "step_id": step,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "tool_result": tool_result,
                    "tool_result_summary": tool_result_summary,
                })

                # NEW: programmatic final for selected tools
                if should_programmatic_finalize(tool_name):
                    final_decision = build_programmatic_final(
                        tool_name, tool_result, user_task)
                    final_answer = final_decision["content"]

                    messages.append({
                        "role": "assistant",
                        "content": final_answer
                    })

                    self.logger.log_step({
                        "event_type": "agent_stop",
                        "step_id": step,
                        "stop_reason": "programmatic_final",
                        "tool_name": tool_name,
                        "final_answer": final_answer,
                        "message_count": len(messages),
                    })

                    print("\n=== AGENT FINAL (PROGRAMMATIC) ===")
                    print(final_answer)
                    return final_answer

                self._append_tool_result(
                    messages=messages,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    tool_result=tool_result
                )

                continue

            # Defensive fallback
            fallback = f"[Unexpected model response] {decision}"

            self.logger.log_step({
                "event_type": "agent_stop",
                "step_id": step,
                "stop_reason": "unexpected_response",
                "raw_decision": decision,
            })

            print(fallback)
            return fallback

        stopped_msg = "Stopped: max steps reached without a final answer."

        self.logger.log_step({
            "event_type": "agent_stop",
            "step_id": self.max_steps,
            "stop_reason": "max_steps_reached",
            "final_answer": stopped_msg,
            "message_count": len(messages),
        })

        print("\n=== AGENT STOPPED ===")
        print(stopped_msg)
        return stopped_msg


if __name__ == "__main__":
    agent = RepoAgent(
        repo_root=settings.repo_root,
        max_steps=settings.max_steps
    )
    agent.run("Where is the auth logic in this repo?")
