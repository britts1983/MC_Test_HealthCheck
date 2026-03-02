import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def save_rotating_screenshot(driver, folder: str, label: str, max_files: int = 20) -> str:
    os.makedirs(folder, exist_ok=True)

    pngs = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(".png")
    ]
    pngs.sort(key=lambda p: os.path.getmtime(p))

    while len(pngs) >= max_files:
        try:
            os.remove(pngs.pop(0))
        except Exception:
            pass

    ts = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{label}.png"
    path = os.path.join(folder, filename)

    driver.save_screenshot(path)
    return path


class JPetStoreSteps:

    def __init__(self, driver, timeout_sec: int = 60, screenshots_dir: str = "artifacts/screenshots"):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout_sec)
        self.screenshots_dir = screenshots_dir

    def shot(self, label: str):
        path = save_rotating_screenshot(self.driver, self.screenshots_dir, label)
        print(f"[SCREENSHOT] {path}")
        return path

    # --------------------------------------------------
    # OPEN SITE (CORRECT FLOW)
    # --------------------------------------------------
    def open_site(self, url: str):

        print("Opening:", url)
        self.driver.get(url)

        # Wait for full page load
        self.wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        time.sleep(2)
        self.shot("01_home")

        # Step 1: Click "Enter the Store"
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Enter the Store"))
        ).click()

        print("Clicked Enter the Store")

        # Step 2: Wait for store homepage
        self.wait.until(
            EC.presence_of_element_located((By.LINK_TEXT, "Sign In"))
        )

        self.shot("02_store_home")
        print("Store page loaded successfully")

    # --------------------------------------------------
    # LOGIN
    # --------------------------------------------------
    def login(self, username: str, password: str):

        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Sign In"))
        ).click()

        self.wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )

        self.driver.find_element(By.NAME, "username").clear()
        self.driver.find_element(By.NAME, "username").send_keys(username)

        self.driver.find_element(By.NAME, "password").clear()
        self.driver.find_element(By.NAME, "password").send_keys(password)

        self.driver.find_element(By.NAME, "signon").click()

        self.wait.until(
            EC.presence_of_element_located((By.LINK_TEXT, "Sign Out"))
        )

        self.shot("03_after_login")
        print("Login completed successfully")

    # --------------------------------------------------
    # BUY FLOW
    # --------------------------------------------------
    def buy_flow(self):

        self.driver.get(
            "https://petstore.octoperf.com/actions/Catalog.action?viewCategory=&categoryId=FISH"
        )

        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//table"))
        )

        self.shot("04_category")

        # Click first product
        self.driver.find_elements(By.XPATH, "//table//tr[position()>1]//a")[0].click()

        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//table"))
        )

        # Click first item
        self.driver.find_elements(By.XPATH, "//table//tr[position()>1]//a")[0].click()

        # Add to cart
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Add to Cart"))
        ).click()

        self.shot("05_cart")

        # Proceed to checkout
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Proceed to Checkout"))
        ).click()

        try:
            self.wait.until(
                EC.element_to_be_clickable((By.NAME, "newOrder"))
            ).click()
        except Exception:
            pass

        self.shot("06_confirm_address")

        # Final submit
        continue_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
        )
        continue_btn.click()

        print("Final submit clicked")

        # Confirmation check
        try:
            self.wait.until(
                lambda d: (
                    "Thank you" in d.page_source
                    or "submitted" in d.page_source
                    or "Order" in d.page_source
                )
            )
        except TimeoutException:
            self.shot("07_submit_timeout")
            raise

        self.shot("07_after_submit")
        print("Purchase flow completed successfully")