import time
import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

LOGIN_URL = os.getenv("LOGIN_URL")
SURVEY_URL = os.getenv("SURVEY_URL")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_TO = os.getenv("EMAIL_TO")

BOT_RUNNING = False

STATUS_LOG = []

browser = None
page = None


def log_status(message, color):

    timestamp = datetime.now().strftime("%H:%M:%S")

    entry = {
        "time": timestamp,
        "message": message,
        "color": color
    }

    STATUS_LOG.insert(0, entry)

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

        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=20
        )

        print("EMAIL RESPONSE:", response.status_code)

    except Exception as e:

        print("EMAIL ERROR:", e)


def launch_browser():

    global browser, page

    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(headless=True)

    context = browser.new_context()

    page = context.new_page()

    print("Browser started")


def login():

    print("Logging in...")

    page.goto(LOGIN_URL)

    page.fill('input[type="email"]', USERNAME)
    page.fill('input[type="password"]', PASSWORD)

    page.click('button[type="submit"]')

    page.wait_for_timeout(5000)

    print("Login complete")


def survey_detected():

    page.goto(SURVEY_URL)

    page.wait_for_timeout(5000)

    html = page.content()

    if "No more surveys" not in html:
        return True

    return False


def run_bot():

    global BOT_RUNNING

    print("BOT STARTED")

    launch_browser()

    login()

    no_survey_counter = 0

    while BOT_RUNNING:

        try:

            print("Checking surveys...")

            found = survey_detected()

            if found:

                log_status("Survey detected", "green")

                send_email("New survey available!")

                print("Survey found → pause 30 minutes")

                time.sleep(1800)

                no_survey_counter = 0

            else:

                log_status("No surveys detected", "red")

                no_survey_counter += 1

                if no_survey_counter >= 3:

                    print("3 failures → pause 10 minutes")

                    time.sleep(600)

                    no_survey_counter = 0

                else:

                    time.sleep(300)

        except Exception as e:

            log_status("Bot error occurred", "orange")

            print("BOT ERROR:", e)

            time.sleep(120)
