import os
import time
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


def launch_browser():

    global browser, page

    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(headless=True)

    context = browser.new_context()

    page = context.new_page()

    print("Browser launched")


def login():

    page.goto(LOGIN_URL)

    page.fill('input[type="email"]', USERNAME)
    page.fill('input[type="password"]', PASSWORD)

    page.click('button[type="submit"]')

    page.wait_for_timeout(5000)

    page.goto(SURVEY_URL)

    log_status("Logged into TryRating", "green")


def instant_listener():

    def handle_response(response):

        url = response.url.lower()

        # listen for task related endpoints
        if "task" in url or "survey" in url or "rating" in url:

            try:

                body = response.text()

                if "No more surveys" not in body:

                    log_status("Survey detected!", "green")

                    send_email("New survey available!")

                    print("Survey detected → pausing 30 minutes")

                    time.sleep(1800)

            except:
                pass

    page.on("response", handle_response)


def fallback_check():

    html = page.content()

    if "No more surveys" not in html:
        log_status("Survey detected (fallback)", "green")
        send_email("New survey available!")


def run_bot():

    global BOT_RUNNING

    launch_browser()

    login()

    instant_listener()

    log_status("Bot started", "green")

    no_survey_counter = 0

    last_check = time.time()

    while BOT_RUNNING:

        try:

            # fallback check every 10 minutes
            if time.time() - last_check > 600:

                fallback_check()

                last_check = time.time()

                no_survey_counter += 1

                if no_survey_counter >= 3:

                    log_status("No surveys after 3 attempts → pause 10 min", "red")

                    time.sleep(600)

                    no_survey_counter = 0

                else:

                    log_status("No surveys detected", "red")

        except Exception as e:

            log_status("Bot error occurred", "orange")

        time.sleep(5)
