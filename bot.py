import time
import smtplib
import os
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

LOGIN_URL = os.getenv("LOGIN_URL")
SURVEY_URL = os.getenv("SURVEY_URL")

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

BOT_RUNNING = False


def send_email():
    try:
        msg = MIMEText("New survey available! Login immediately.")
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


def create_driver():

    chrome_options = Options()

    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # correct path for Render
    chrome_options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    return driver


def check_surveys():

    print("Checking survey page...")

    driver = create_driver()

    try:

        driver.get(LOGIN_URL)
        time.sleep(3)

        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button").click()

        time.sleep(5)

        driver.get(SURVEY_URL)
        time.sleep(3)

        page = driver.page_source

        # TEST MODE (always send email)
        if True:
            print("Survey detected!")
            send_email()

        # REAL MODE (use this later)
        # if "No more surveys" not in page:
        #     print("Survey detected!")
        #     send_email()
        # else:
        #     print("No surveys.")

    except Exception as e:
        print("ERROR DURING CHECK:", e)

    finally:
        driver.quit()


def run_bot():

    global BOT_RUNNING

    while BOT_RUNNING:

        try:
            check_surveys()
        except Exception as e:
            print("BOT ERROR:", e)

        # check every 5 minutes
        time.sleep(300)