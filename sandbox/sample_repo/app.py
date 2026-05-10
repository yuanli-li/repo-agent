from auth import verify_token


def login(token: str) -> str:
    if verify_token(token):
        return "login success"
    return "login failed"


if __name__ == "__main__":
    print(login("secret123"))
