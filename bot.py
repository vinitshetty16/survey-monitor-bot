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

# set True to test email system
TEST_MODE = True


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


def login_and_check():

    print("Checking survey page...")

    session = requests.Session()

    login_payload = {
        "username": USERNAME,
        "password": PASSWORD
    }

    # login
    session.post(LOGIN_URL, data=login_payload)

    # open survey page
    response = session.get(SURVEY_URL)

    page = response.text

    # TEST MODE
    if TEST_MODE:
        if "No more surveys" in page:
            print("TEST: No surveys detected")
            send_email("SMTP test successful. Bot detected 'No more surveys'.")

    # REAL MODE
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
            login_and_check()
        except Exception as e:
            print("BOT ERROR:", e)

        # check every 5 minutes
        time.sleep(300)