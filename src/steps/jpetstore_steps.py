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
    # HARDENED open_site WITH DEBUG DUMP
    # --------------------------------------------------
    def open_site(self, url: str):

        print("Opening:", url)
        self.driver.get(url)

        # Wait until page fully loads
        self.wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        time.sleep(3)  # headless render buffer

        print("Current URL:", self.driver.current_url)
        print("Page title:", self.driver.title)

        # Screenshot initial page
        self.shot("01_home")

        # Dump page source for debugging
        debug_file = "artifacts/debug_page.html"
        os.makedirs("artifacts", exist_ok=True)
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

        print(f"Page source dumped to {debug_file}")

        try:
            # More reliable XPath locator
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(text(),'Sign')]")
                )
            )
            print("Sign link found.")
        except TimeoutException:
            print("Sign link NOT found.")
            self.shot("01_home_signin_not_found")
            raise

    # --------------------------------------------------
    # LOGIN
    # --------------------------------------------------
    def login(self, username: str, password: str):

        self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Sign')]"))
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
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(text(),'Sign Out')]")
            )
        )

        self.shot("02_after_login")
        print("Login completed")

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

        self.shot("03_category")

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

        self.shot("04_cart")

        # Checkout
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Proceed to Checkout"))
        ).click()

        try:
            self.wait.until(
                EC.element_to_be_clickable((By.NAME, "newOrder"))
            ).click()
        except Exception:
            pass

        self.shot("05_confirm_address")

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
            print("Order confirmation detected.")
        except TimeoutException:
            print("Order confirmation NOT detected.")
            self.shot("06_submit_timeout")
            raise

        self.shot("06_after_submit")
        print("Flow completed successfully")