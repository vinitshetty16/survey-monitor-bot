import time
import os
import requests
import threading

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

LOGIN_URL = os.getenv("LOGIN_URL")
SURVEY_URL = os.getenv("SURVEY_URL")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_TO = os.getenv("EMAIL_TO")

BOT_RUNNING = True

session = requests.Session()
logged_in = False

_status_lock = threading.Lock()
_status = {
    "running": False,
    "logged_in": False,
    "no_survey_streak": 0,
    "last_check_at": None,      # epoch seconds
    "last_result": None,        # "no_surveys" | "survey_detected" | "error"
    "last_error": None,
    "last_email_at": None,      # epoch seconds
    "next_check_at": None,      # epoch seconds
    "sleep_reason": None,       # "poll_5m" | "backoff_15m" | "cooldown_30m" | "error_5m"
}


def get_status():
    """Safe snapshot for the Flask dashboard."""
    with _status_lock:
        s = dict(_status)

    now = time.time()
    nca = s.get("next_check_at")
    if isinstance(nca, (int, float)):
        s["next_check_in_s"] = max(0, int(nca - now))
    else:
        s["next_check_in_s"] = None
    return s


def _set_status(**updates):
    with _status_lock:
        _status.update(updates)


def send_email(message):

    url = "https://api.resend.com/emails"

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "from": "Survey Bot <onboarding@resend.dev>",
        "to": [EMAIL_TO],
        "subject": "Survey Alert",
        "html": f"<p>{message}</p>"
    }

    try:

        response = requests.post(url, json=data, headers=headers)

        print("EMAIL RESPONSE:", response.status_code, response.text)

    except Exception as e:
        print("EMAIL ERROR:", e)


def _page_has_no_surveys(page_text: str) -> bool:
    # The UI message shown when nothing is available.
    return "no more surveys" in (page_text or "").lower()


def _page_looks_like_login(page_text: str) -> bool:
    # Heuristic so we can re-login if the session expires.
    t = (page_text or "").lower()
    return ("login to" in t and "password" in t) or ("forgot password" in t)


def login():

    global logged_in

    print("Logging in...")
    _set_status(last_error=None)

    payload = {
        "email": USERNAME,
        "password": PASSWORD
    }

    response = session.post(LOGIN_URL, data=payload)

    print("Login status:", response.status_code)

    if response.status_code == 200:
        logged_in = True
        _set_status(logged_in=True)
        print("Login successful")
    else:
        print("Login failed")
        _set_status(logged_in=False)


def check_surveys() -> bool:

    global logged_in

    if not logged_in:
        login()

    print("Checking survey page...")
    _set_status(last_check_at=time.time(), last_error=None)

    response = session.get(SURVEY_URL)

    page = response.text

    print("Page checked")

    if _page_looks_like_login(page):
        print("Session looks logged out; re-logging in...")
        logged_in = False
        login()
        response = session.get(SURVEY_URL)
        page = response.text

    if _page_has_no_surveys(page):
        print("No surveys found (No more surveys message present).")
        _set_status(last_result="no_surveys")
        return False

    print("Survey detected! (No more surveys message NOT present)")
    _set_status(last_result="survey_detected")
    return True


def run_bot():

    # Requirements:
    # - Check every 5 mins
    # - If "No more surveys" is present: do nothing
    # - Do this 3 times, then wait 15 mins, then again start
    # - If message is gone: send email, then wait 30 mins and look again
    no_survey_streak = 0
    _set_status(running=True, no_survey_streak=0, sleep_reason=None)

    while BOT_RUNNING:
        try:
            has_survey = check_surveys()

            if has_survey:
                no_survey_streak = 0
                _set_status(no_survey_streak=0)
                send_email("New survey available! Login immediately.")
                _set_status(last_email_at=time.time())
                # After an alert, back off for 30 minutes.
                sleep_s = 30 * 60
                sleep_reason = "cooldown_30m"
            else:
                no_survey_streak += 1
                _set_status(no_survey_streak=no_survey_streak)
                if no_survey_streak >= 3:
                    no_survey_streak = 0
                    _set_status(no_survey_streak=0)
                    # After 3 consecutive "no survey" checks, wait 15 minutes.
                    sleep_s = 15 * 60
                    sleep_reason = "backoff_15m"
                else:
                    # Regular polling interval.
                    sleep_s = 5 * 60
                    sleep_reason = "poll_5m"

        except Exception as e:
            print("BOT ERROR:", e)
            _set_status(last_result="error", last_error=str(e))
            # If something transient fails, try again in 5 minutes.
            sleep_s = 5 * 60
            sleep_reason = "error_5m"

        # Sleep in small chunks so /pause can stop promptly.
        _set_status(next_check_at=time.time() + sleep_s, sleep_reason=sleep_reason)
        remaining = sleep_s
        while BOT_RUNNING and remaining > 0:
            step = min(5, remaining)
            time.sleep(step)
            remaining -= step

    _set_status(running=False, next_check_at=None, sleep_reason=None)
