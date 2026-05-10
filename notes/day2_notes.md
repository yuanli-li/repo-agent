# Day 2 Notes

## What I completed today
Today I focused on building the tool layer for my minimal repo agent.

I implemented the following tools:

- `read_file.py`
- `search_code.py`
- `run_command.py`
- `tool_registry.py`

The main goal was not to make the agent “smart” yet, but to give it reliable and controlled ways to interact with a repository.

## What each tool does

### `read_file`
This tool reads a file inside the repository with basic path safety checks.
It supports reading a file by relative path and optional line ranges.

### `search_code`
This tool searches the repository using `ripgrep (rg)`.
It returns matching file paths and line numbers, which will later help the agent locate relevant code before reading files directly.

### `run_command`
This tool runs only allowlisted commands inside the repository.
Right now, it only supports a very small set of safe commands, such as:

- `pytest`
- `python -m pytest`
- `ls`
- `pwd`

This is important because I do not want the agent to execute arbitrary shell commands.

### `tool_registry`
This file acts as the central dispatcher for the tools.
It maps tool names to actual Python functions and makes it easier for the agent loop to execute tools by name later.

## What I learned today

### 1. Tools are the hands and feet of the agent
The model itself cannot read files or run commands.
It can only decide what tool should be used.
My Python code is what actually executes the tool.

### 2. Safety boundaries must exist from the beginning
I should not wait until later to think about security.
Even in a small learning project, command execution needs strict allowlists, and file access must stay inside the repo root.

### 3. Tool output structure matters
The tools should return structured dictionaries instead of messy free-form strings.
This will make it much easier for the future agent loop to use the results consistently.

## Problems and challenges
Some parts were trickier than they first looked:

- making sure file reads cannot escape the repository root
- deciding how much output to return from `search_code`
- keeping `run_command` safe without making it useless
- designing tool return values that are simple but still informative

## What is working now
At the end of Day 2, I now have a basic but functional tool layer that I can manually test.

I can:
- read repository files
- search code by keyword
- run safe commands such as `pytest`

## What is still missing
I still do not have the actual agent loop yet.

The project is missing:
- `call_model()` behavior
- message history management
- tool-call → execute → observe loop
- final answer generation

## Plan for Day 3
Tomorrow I want to connect the tool layer to a minimal agent loop.

Specifically, I want to:
1. design the minimal `call_model()` interface
2. build the first working loop in `agent.py`
3. append tool results back into `messages`
4. make the agent stop correctly after a final answer or max steps

## Summary
Day 2 was about turning the project from an empty scaffold into something that can actually interact with a repository in controlled ways.

Today’s progress was not flashy, but it was foundational.
I now have the execution layer that the future agent will rely on.