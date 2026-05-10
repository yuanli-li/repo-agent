from app.config import settings


def main():
    print("Repo Agent v0")
    print("Repo root:", settings.repo_root)
    print("Max steps:", settings.max_steps)


if __name__ == "__main__":
    main()
