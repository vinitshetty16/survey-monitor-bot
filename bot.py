import time
import smtplib
import os
import requests
from email.mime.text import MIMEText


USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

LOGIN_URL = os.getenv("LOGIN_URL")
SURVEY_URL = os.getenv("SURVEY_URL")

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")


BOT_RUNNING = False
TEST_MODE = True  # set False after testing email


session = requests.Session()
logged_in = False


def send_email(message):

    try:
        msg = MIMEText(message)
        msg["Subject"] = "Survey Alert"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("EMAIL SENT SUCCESSFULLY")

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

    print("PAGE DEBUG:")
    print(page[:1000])

    if TEST_MODE:

        print("TEST MODE: sending email")
        send_email("Survey bot SMTP test successful.")

    else:

        if "No more surveys" not in page:
            print("Survey detected!")
            send_email("New survey available! Login immediately.")

        else:
            print("No surveys.")


def run_bot():

    global BOT_RUNNING

    while BOT_RUNNING:

        try:
            check_surveys()

        except Exception as e:
            print("BOT ERROR:", e)


        time.sleep(60)
