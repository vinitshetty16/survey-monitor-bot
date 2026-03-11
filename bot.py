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


def check_surveys():

    global logged_in

    if not logged_in:
        login()

    print("Checking survey page...")

    response = session.get(SURVEY_URL)

    page = response.text

    print("Page checked")

    #if "No more surveys" not in page:
    if True:

        print("Survey detected!")

        send_email("New survey available! Login immediately.")

    else:

        print("No surveys found")


def run_bot():

    while BOT_RUNNING:

        try:

            check_surveys()

        except Exception as e:

            print("BOT ERROR:", e)

        time.sleep(300)  # 5 minutes