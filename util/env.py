# Enter username and password for env if needed
from dotenv import load_dotenv
import os

def create_env():
    print("Please log in to Re-Leased:\n")
    e = input("[Email] ")
    p = input("[Password] ")

    with open(".env", "w") as f:
        f.write(f'EMAIL = "{e}"\nPASSWORD = "{p}"')


def env() -> tuple[str, str]:
    while True:
        load_dotenv()

        if os.getenv("EMAIL") == None or os.getenv("PASSWORD") == None:
            print("You are not logged in to Re-Leased.\n")
            create_env()
        else: return os.getenv("EMAIL"), os.getenv("PASSWORD")