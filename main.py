import argparse
from app.agent import RepoAgent
from app.config import settings


def main():
    parser = argparse.ArgumentParser(description="Minimal Repo Agent v0")
    parser.add_argument("task", type=str, help="User task for the repo agent")
    args = parser.parse_args()

    agent = RepoAgent(
        repo_root=settings.repo_root,
        max_steps=settings.max_steps
    )
    result = agent.run(args.task)

    print("\n=== FINAL RESULT ===")
    print(result)


if __name__ == "__main__":
    main()
