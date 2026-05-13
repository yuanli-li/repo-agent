# Repo Agent

A minimal repo agent project for learning AI agent fundamentals.

## Week 1 Goal

- understand tool use
- build project structure
- prepare a sample repository
- get ready for a minimal agent loop

## Run

## Current Workflow

```mermaid
flowchart TD
    A[User enters a repository question or task] --> B[Agent starts a new session]
    B --> C[Initialize conversation history]
    C --> D[Model decides next step]

    D --> E{Decision type}

    E -->|Tool Call| F[Choose one tool]
    E -->|Final Answer| G[Return final response and stop]

    F --> H{Available tools}
    H -->|Search code| I[Search repository for keywords or symbols]
    H -->|Read file| J[Read a specific file inside the repo]
    H -->|Run command| K[Run a safe allowlisted command]

    I --> L[Tool result returned]
    J --> L
    K --> L

    L --> M[Write tool call into conversation history]
    M --> N[Write tool result into conversation history]
    N --> O[Write step trace into session log]
    O --> P[Model sees updated context]
    P --> D

    G --> Q[Write stop event into session log]
    Q --> R[Print final answer]