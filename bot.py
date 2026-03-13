import time
import os
import requests

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

LOGIN_URL = os.getenv("LOGIN_URL")
SURVEY_URL = os.getenv("SURVEY_URL")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_TO = os.getenv("EMAIL_TO")

BOT_RUNNING = True

session = requests.Session()
logged_in = False


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

    payload = {
        "email": USERNAME,
        "password": PASSWORD
    }

    response = session.post(LOGIN_URL, data=payload)

    print("Login status:", response.status_code)

    if response.status_code == 200:
        logged_in = True
        print("Login successful")
    else:
        print("Login failed")


def check_surveys() -> bool:

    global logged_in

    if not logged_in:
        login()

    print("Checking survey page...")

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
        return False

    print("Survey detected! (No more surveys message NOT present)")
    return True


def run_bot():

    # Requirements:
    # - Check every 5 mins
    # - If "No more surveys" is present: do nothing
    # - Do this 3 times, then wait 15 mins, then again start
    # - If message is gone: send email, then wait 30 mins and look again
    no_survey_streak = 0

    while BOT_RUNNING:
        try:
            has_survey = check_surveys()

            if has_survey:
                no_survey_streak = 0
                send_email("New survey available! Login immediately.")
                # After an alert, back off for 30 minutes.
                sleep_s = 30 * 60
            else:
                no_survey_streak += 1
                if no_survey_streak >= 3:
                    no_survey_streak = 0
                    # After 3 consecutive "no survey" checks, wait 15 minutes.
                    sleep_s = 15 * 60
                else:
                    # Regular polling interval.
                    sleep_s = 5 * 60

        except Exception as e:
            print("BOT ERROR:", e)
            # If something transient fails, try again in 5 minutes.
            sleep_s = 5 * 60

        # Sleep in small chunks so /pause can stop promptly.
        remaining = sleep_s
        while BOT_RUNNING and remaining > 0:
            step = min(5, remaining)
            time.sleep(step)
            remaining -= step
