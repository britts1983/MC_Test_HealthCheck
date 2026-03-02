import os
import time
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def save_rotating_screenshot(driver, folder: str, label: str, max_files: int = 30):
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
    path = os.path.join(folder, f"{ts}_{label}.png")
    driver.save_screenshot(path)
    return path


class JPetStoreSteps:
    def __init__(self, driver, timeout_sec=120, screenshots_dir="artifacts/screenshots"):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout_sec)
        self.screenshots_dir = screenshots_dir

    def shot(self, label):
        path = save_rotating_screenshot(self.driver, self.screenshots_dir, label)
        print(f"[SCREENSHOT] {path}")
        return path

    def dump_page(self):
        with open("artifacts/debug_page.html", "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

    def wait_ready(self):
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(1)

    # -------------------------------
    # OPEN SITE
    # -------------------------------
    def open_site(self, url):
        print("Opening:", url)
        self.driver.get(url)
        self.wait_ready()
        self.shot("01_home")

        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Enter the Store"))).click()
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign In")))
        self.wait_ready()
        self.shot("02_store_home")
        print("Store loaded")

    # -------------------------------
    # LOGIN
    # -------------------------------
    def login(self, username, password):
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sign In"))).click()
        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))

        self.driver.find_element(By.NAME, "username").clear()
        self.driver.find_element(By.NAME, "username").send_keys(username)

        self.driver.find_element(By.NAME, "password").clear()
        self.driver.find_element(By.NAME, "password").send_keys(password)

        self.driver.find_element(By.NAME, "signon").click()

        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign Out")))
        self.wait_ready()
        self.shot("03_after_login")
        print("Login successful")

    # -------------------------------
    # BUY FLOW (SIMPLIFIED & STABLE)
    # -------------------------------
    def buy_flow(self):
        try:
            # Click FISH category
            self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='categoryId=FISH']"))
            ).click()

            self.wait_ready()
            self.shot("04_fish_category")

            # Click FIRST product row (ignore URL pattern)
            product_link = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table//tr[2]//a")
                )
            )
            product_link.click()

            self.wait_ready()
            self.shot("05_product_page")

            # Click FIRST item row
            item_link = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table//tr[2]//a")
                )
            )
            item_link.click()

            # Add to cart
            self.wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Add to Cart"))
            ).click()

            self.wait_ready()
            self.shot("06_cart")

            # Proceed to checkout
            self.wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Proceed to Checkout"))
            ).click()

            # Confirm order
            try:
                self.wait.until(
                    EC.element_to_be_clickable((By.NAME, "newOrder"))
                ).click()
            except:
                pass

            self.wait_ready()
            self.shot("07_checkout")

            # Final submit
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
            ).click()

            # Wait for confirmation
            self.wait.until(lambda d: "Order" in d.page_source or "Thank you" in d.page_source)

            self.wait_ready()
            self.shot("08_success")

            print("Purchase completed successfully")
            return "Order placed successfully"

        except Exception as e:
            self.shot("99_failure")
            self.dump_page()
            raise