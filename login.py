from pathlib import Path

import keyring
import requests
from bs4 import BeautifulSoup


SERVICE = "WIFI"

PORTAL = (
    "https://internet.lpu.in/24online/webpages/client.jsp"
)

LOGIN_ENDPOINT = (
    "https://internet.lpu.in/24online/servlet/E24onlineHTTPClient"
)

USERNAME_FILE = Path.home() / ".lpu_username"

TIMEOUT = 8


def get_credentials():
    """Load username and password."""
    if not USERNAME_FILE.exists():
        print("✗ Credentials not configured")
        print("  Run: setup")
        return None, None

    username = USERNAME_FILE.read_text(
        encoding="utf-8"
    ).strip()

    if not username:
        print("✗ Username is empty")
        print("  Run: setup")
        return None, None

    password = keyring.get_password(
        SERVICE,
        username
    )

    if not password:
        print("✗ Password not found")
        print("  Run: setup")
        return None, None

    return username, password


def get_form_data(html):
    """Extract the current LPU login form."""
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    form = soup.find(
        "form",
        attrs={
            "action":
            "/24online/servlet/E24onlineHTTPClient"
        }
    )

    if form is None:
        return None

    data = {}

    for element in form.find_all(
        ["input", "select", "textarea"]
    ):
        name = element.get("name")

        if not name:
            continue

        
        if element.name == "input":

            input_type = element.get(
                "type",
                "text"
            ).lower()

         
            if input_type in {
                "submit",
                "button",
                "reset",
                "file"
            }:
                continue

            if input_type in {
                "checkbox",
                "radio"
            }:
                if not element.has_attr("checked"):
                    continue

            data[name] = element.get(
                "value",
                ""
            )

        elif element.name == "select":

            selected = element.find(
                "option",
                selected=True
            )

            data[name] = (
                selected.get("value", "")
                if selected
                else ""
            )

     
        else:
            data[name] = element.text or ""

    return data


def is_logged_in(html):
    """Detect the authenticated LPU page."""
    text = html.lower()

    indicators = [
        "you have successfully logged in",
        "click here to check your usage",
        'name=\'logout\'',
        'value=\'logout\'',
        ">logout<",
    ]

    return any(
        indicator in text
        for indicator in indicators
    )


def is_login_page(html):
    """Detect whether authentication is required."""
    text = html.lower()

    indicators = [
        'name="password"',
        'type="password"',
        "staff/student login",
        "i agree with terms",
    ]

    return any(
        indicator in text
        for indicator in indicators
    )


def response_contains_login_error(html):
    """Detect common authentication errors."""
    text = html.lower()

    errors = [
        "invalid password",
        "invalid username",
        "authentication failed",
        "login failed",
        "incorrect password",
        "incorrect username",
        "invalid credentials",
    ]

    return any(
        error in text
        for error in errors
    )


def check_basic_connectivity():
    """Check whether the LPU portal is reachable."""
    try:
        response = requests.get(
            PORTAL,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        return response

    except requests.Timeout:
        return None

    except requests.ConnectionError:
        return None


def main():

    username, password = get_credentials()

    if not username or not password:
        return 1

    print(
        "Checking Wi-Fi...",
        end=" ",
        flush=True
    )

 
    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/153.0 Safari/537.36"
        )
    })

    try:


        response = session.get(
            PORTAL,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

        initial_html = response.text

     

        if is_logged_in(initial_html):

            print("✓ Already logged in")
            return 0



        if not is_login_page(initial_html):

            print("⚠ Unexpected portal response")
            print(
                f"  URL: {response.url}"
            )
            return 1

    

        form_data = get_form_data(
            initial_html
        )

        if form_data is None:

            print("✗ Login form not found")
            return 1

     

        form_data.update({

            "mode": "191",

            "checkClose": "1",

            "username": username,

            "password": password,

            "loginotp": "false",

            "logincaptcha": "false",

            "registeruserotp": "false",

            "registercaptcha": "false",
        })

       

        login_response = session.post(

            LOGIN_ENDPOINT,

            data=form_data,

            headers={
                "Referer": response.url,
                "Origin":
                    "https://internet.lpu.in",
            },

            timeout=TIMEOUT,

            allow_redirects=True,
        )

      

        result = login_response.text

        if is_logged_in(result):

            print("✓ Login successful")
            return 0

        if response_contains_login_error(result):

            print("✗ Login failed")
            print(
                "  Check your LPU username/password."
            )
            return 1

       

        if (
            login_response.url
            != response.url
        ):

            print(
                "⚠ Authentication response "
                "was unexpected"
            )

            print(
                f"  Final URL: "
                f"{login_response.url}"
            )

            return 1

      

        print("⚠ Authentication state unclear")
        print(
            f"  HTTP status: "
            f"{login_response.status_code}"
        )

        return 1

    except requests.Timeout:

        print("✗ Timeout")

        print(
            "  LPU portal did not respond."
        )

        print(
            "  Make sure you are connected "
            "to LPU Wi-Fi."
        )

        return 1

    except requests.ConnectionError:

        print("✗ Cannot reach LPU portal")

        print(
            "  Connect to LPU Wi-Fi first."
        )

        return 1

    except requests.HTTPError as e:

        print("✗ HTTP error")

        print(f"  {e}")

        return 1

    except requests.RequestException as e:

        print("✗ Network error")

        print(f"  {e}")

        return 1

    except Exception as e:

        print("✗ Unexpected error")

        print(f"  {e}")

        return 1


if __name__ == "__main__":
    raise SystemExit(main())