from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os


def create_driver(headless: bool, timeout_sec: int):

    options = webdriver.ChromeOptions()

    # 🔥 Disable password popups
    options.add_argument("--incognito")

    options.add_argument("--disable-save-password-bubble")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")

    # Remove automation banner
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # CI stability flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1400,900")

    service = Service(os.path.abspath("drivers/chromedriver"))

    driver = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(timeout_sec)

    return driver