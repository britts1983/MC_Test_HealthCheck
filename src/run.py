import argparse
import sys
import time
import traceback

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from steps.jpetstore_steps import JPetStoreSteps


SCREENSHOTS_DIR = "artifacts/screenshots"


def create_driver(headless=True):
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # IMPORTANT for macOS stability
    options.add_argument("--remote-allow-origins=*")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(120)
    return driver


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--url")
    parser.add_argument("--username")
    parser.add_argument("--password")

    args = parser.parse_args()

    driver = None
    start = time.time()

    try:
        driver = create_driver(headless=args.headless)

        steps = JPetStoreSteps(
            driver,
            timeout_sec=args.timeout,
            screenshots_dir=SCREENSHOTS_DIR
        )

        steps.open_site(args.url)
        steps.login(args.username, args.password)
        order_info = steps.buy_flow()

        print("Status: PASS")
        print("Duration:", round(time.time() - start, 2))
        print("FINAL STATUS: PASS")

        sys.exit(0)

    except Exception as e:
        print("Error:", e)
        print("------ TRACEBACK ------")
        traceback.print_exc()
        print("-----------------------")
        print("Status: FAIL")
        print("Duration:", round(time.time() - start, 2))
        print("FINAL STATUS: FAIL")

        sys.exit(1)

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()