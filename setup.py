import getpass
import keyring
from pathlib import Path

SERVICE = "WIFI"
USERNAME_FILE = Path.home() / ".lpu_username"

username = input(
    "Enter your LPU username: "
).strip()

if "@" not in username:
    username = username + "@lpu.com"

password = getpass.getpass(
    "Enter your LPU password: "
)

USERNAME_FILE.write_text(
    username,
    encoding="utf-8"
)

keyring.set_password(
    SERVICE,
    username,
    password
)

print("\nCredentials saved securely.")
print("Username:", username)
print(
    "Password stored in Windows Credential Manager."
)
print("\nYou can now use: login")