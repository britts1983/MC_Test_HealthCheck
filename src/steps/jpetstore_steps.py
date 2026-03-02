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

    def __init__(self, driver, timeout_sec: int = 120, screenshots_dir: str = "artifacts/screenshots"):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout_sec)
        self.screenshots_dir = screenshots_dir

    def shot(self, label: str):
        path = save_rotating_screenshot(self.driver, self.screenshots_dir, label)
        print(f"[SCREENSHOT] {path}")
        return path

    # -------------------------------
    # OPEN SITE
    # -------------------------------
    def open_site(self, url: str):

        print("Opening:", url)
        self.driver.get(url)

        self.wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        time.sleep(2)
        self.shot("01_home")

        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Enter the Store"))
        ).click()

        self.wait.until(
            EC.presence_of_element_located((By.LINK_TEXT, "Sign In"))
        )

        self.shot("02_store_home")
        print("Store loaded")

    # -------------------------------
    # LOGIN
    # -------------------------------
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
        print("Login successful")

    # -------------------------------
    # BUY FLOW (FINAL STABLE)
    # -------------------------------
    def buy_flow(self):

        # Go to FISH category
        self.driver.get(
            "https://petstore.octoperf.com/actions/Catalog.action?viewCategory=&categoryId=FISH"
        )

        # Wait until product links exist
        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@href,'Product.action')]")
            )
        )

        self.shot("04_category")

        # Click first product safely
        products = self.driver.find_elements(By.XPATH, "//a[contains(@href,'Product.action')]")
        products[0].click()

        # Wait for item links
        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@href,'Item.action')]")
            )
        )

        # Click first item safely
        items = self.driver.find_elements(By.XPATH, "//a[contains(@href,'Item.action')]")
        items[0].click()

        # Add to cart
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Add to Cart"))
        ).click()

        self.shot("05_cart")

        # Proceed to checkout
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Proceed to Checkout"))
        ).click()

        # Sometimes there is intermediate page
        try:
            self.wait.until(
                EC.element_to_be_clickable((By.NAME, "newOrder"))
            ).click()
        except Exception:
            pass

        self.shot("06_confirm_page")

        # Final submit
        submit_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
        )
        submit_btn.click()

        print("Submit clicked")

        # Confirmation wait
        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Order')]")
            )
        )

        self.shot("07_success")

        print("Purchase completed successfully")
        return "Order placed successfully"