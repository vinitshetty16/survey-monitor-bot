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

    msg = MIMEText("New survey available! Login immediately.")
    msg["Subject"] = "Survey Alert"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_FROM, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()


def create_driver():

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    return driver


def check_surveys():

    print("Checking survey page...")

    driver = create_driver()

    driver.get(LOGIN_URL)
    time.sleep(3)

    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button").click()

    time.sleep(5)

    driver.get(SURVEY_URL)
    time.sleep(3)

    page = driver.page_source

    #if "No more surveys" not in page:
    if True:
        print("Survey detected!")
        send_email()
    else:
        print("No surveys.")

    driver.quit()


def run_bot():

    global BOT_RUNNING

    while BOT_RUNNING:

        try:
            check_surveys()
        except Exception as e:
            print("Error:", e)

        time.sleep(300)