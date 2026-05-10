import json
from typing import Any, Dict, List

from app.config import settings
from app.prompts import SYSTEM_PROMPT
from app.llm_client import call_model
from app.tool_registry import execute_tool, get_tool_schemas


class RepoAgent:
    def __init__(self, repo_root: str, max_steps: int = 6):
        self.repo_root = repo_root
        self.max_steps = max_steps
        self.tools = get_tool_schemas()

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

    def run(self, user_task: str) -> str:
        messages = self._make_initial_messages(user_task)

        print("\n=== AGENT START ===")
        print("Task:", user_task)

        for step in range(1, self.max_steps + 1):
            print(f"\n--- Step {step} ---")

            decision = call_model(
                messages=messages,
                system_prompt=SYSTEM_PROMPT,
                tools=self.tools
            )

            print("Model decision:", decision)

            if decision["type"] == "final":
                final_answer = decision["content"]
                messages.append(
                    {
                        "role": "assistant",
                        "content": final_answer
                    }
                )
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

                self._append_tool_result(
                    messages=messages,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    tool_result=tool_result
                )

                continue

            # Defensive fallback
            fallback = f"[Unexpected model response] {decision}"
            print(fallback)
            return fallback

        stopped_msg = "Stopped: max steps reached without a final answer."
        print("\n=== AGENT STOPPED ===")
        print(stopped_msg)
        return stopped_msg


if __name__ == "__main__":
    agent = RepoAgent(
        repo_root=settings.repo_root,
        max_steps=settings.max_steps
    )
    agent.run("Where is the auth logic in this repo?")
