import os
import time
import requests
from datetime import datetime

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

LOGIN_URL = os.getenv("LOGIN_URL")
SURVEY_URL = os.getenv("SURVEY_URL")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_TO = os.getenv("EMAIL_TO")

BOT_RUNNING = False

STATUS_LOG = []

session = requests.Session()
logged_in = False


def log_status(message, color):

    STATUS_LOG.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": message,
        "color": color
    })

    if len(STATUS_LOG) > 30:
        STATUS_LOG.pop()


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
        requests.post(url, json=data, headers=headers, timeout=20)
    except:
        pass


def login():

    global logged_in

    payload = {
        "email": USERNAME,
        "password": PASSWORD
    }

    response = session.post(LOGIN_URL, data=payload)

    if response.status_code == 200:

        logged_in = True

        log_status("Login successful", "green")

    else:

        log_status("Login failed", "orange")


def check_surveys():

    response = session.get(SURVEY_URL)

    page = response.text

    print("PAGE CHECKED")

    if "No more surveys" in page:

        return False

    else:

        return True


def run_bot():

    global BOT_RUNNING

    log_status("Bot started", "green")

    login()

    no_survey_counter = 0

    while BOT_RUNNING:

        try:

            found = check_surveys()

            if found:

                log_status("Survey detected", "green")

                send_email("New survey available!")

                print("Survey detected → pausing 30 minutes")

                time.sleep(1800)

                no_survey_counter = 0

            else:

                log_status("No surveys detected", "red")

                no_survey_counter += 1

                if no_survey_counter >= 3:

                    log_status("3 attempts failed → pause 15 minutes", "red")

                    time.sleep(900)

                    no_survey_counter = 0

                else:

                    time.sleep(300)

        except Exception:

            log_status("Bot error occurred", "orange")

            time.sleep(120)
