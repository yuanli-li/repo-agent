1. Key Takeaways
LLMs do not actually call tools: I learned that the model itself cannot interact with the external world; it only generates the intent to do so.

Tool Calling Mechanism: Tool calling is a process where the model "suggests" a function call, but the actual execution is performed by the underlying code.

ReAct Pattern: I grasped the Thought → Action → Observation loop, which is the standard reasoning framework for autonomous agents.

2. Progress Made
Project Environment: Successfully initialized the repo-agent project directory and architecture.

Virtual Environment: Set up a Python virtual environment (venv) for dependency isolation.

Sandbox Creation: Built the sample_repo to serve as a controlled environment for agent testing.

Testing Infrastructure: Verified the sandbox environment by successfully running pytest.