import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def save_rotating_screenshot(driver, folder: str, label: str, max_files: int = 30) -> str:
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

    def dump_page(self, filename: str = "artifacts/debug_page.html"):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
        print(f"Page source dumped to {filename}")

    def wait_ready(self):
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(1)

    def is_logged_in(self) -> bool:
        try:
            self.driver.find_element(By.LINK_TEXT, "Sign Out")
            return True
        except Exception:
            return False

    # -------------------------------
    # OPEN SITE (REAL USER FLOW)
    # -------------------------------
    def open_site(self, url: str):
        print("Opening:", url)
        self.driver.get(url)
        self.wait_ready()
        self.shot("01_home")

        # Must click "Enter the Store"
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Enter the Store"))).click()

        # Wait until store home is ready (Sign In link visible)
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign In")))
        self.wait_ready()
        self.shot("02_store_home")
        print("Store loaded")

    # -------------------------------
    # LOGIN
    # -------------------------------
    def login(self, username: str, password: str):
        # Click Sign In
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sign In"))).click()

        # Wait for login form
        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))

        u = self.driver.find_element(By.NAME, "username")
        p = self.driver.find_element(By.NAME, "password")

        u.clear()
        u.send_keys(username)

        p.clear()
        p.send_keys(password)

        self.driver.find_element(By.NAME, "signon").click()

        # Confirm login by waiting Sign Out
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign Out")))
        self.wait_ready()
        self.shot("03_after_login")
        print("Login successful")

    # -------------------------------
    # BUY FLOW (HARDENED)
    # -------------------------------
    def buy_flow(self):
        """
        FIX:
        - Do NOT open category by direct URL.
        - Click category link (FISH) from UI.
        - Retry once if headless render/network is slow.
        """

        for attempt in range(1, 3):  # 2 attempts
            try:
                if not self.is_logged_in():
                    raise TimeoutException("Not logged in (Sign Out not found).")

                # Click FISH category from left menu (real user)
                self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "FISH"))).click()

                # Wait product list exists
                self.wait.until(
                    lambda d: len(d.find_elements(By.XPATH, "//a[contains(@href,'Product.action')]")) > 0
                )
                self.wait_ready()
                self.shot("04_fish_category")

                # Click first product
                products = self.driver.find_elements(By.XPATH, "//a[contains(@href,'Product.action')]")
                products[0].click()

                # Wait item list exists
                self.wait.until(
                    lambda d: len(d.find_elements(By.XPATH, "//a[contains(@href,'Item.action')]")) > 0
                )
                self.wait_ready()
                self.shot("05_product_page")

                # Click first item
                items = self.driver.find_elements(By.XPATH, "//a[contains(@href,'Item.action')]")
                items[0].click()

                # Add to cart
                self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Add to Cart"))).click()
                self.wait_ready()
                self.shot("06_cart")

                # Checkout
                self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Proceed to Checkout"))).click()

                # Sometimes intermediate confirm page exists
                try:
                    self.wait.until(EC.element_to_be_clickable((By.NAME, "newOrder"))).click()
                except Exception:
                    pass

                self.wait_ready()
                self.shot("07_checkout")

                # Final submit
                self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))).click()

                # Confirmation
                self.wait.until(
                    lambda d: ("Thank you" in d.page_source) or ("Order" in d.page_source)
                )
                self.wait_ready()
                self.shot("08_success")

                print("Purchase completed successfully")
                return "Order placed successfully"

            except Exception as e:
                print(f"[BUY_FLOW] Attempt {attempt} failed: {e}")
                self.shot(f"99_buyflow_fail_attempt_{attempt}")
                self.dump_page()

                # retry once with refresh
                if attempt < 2:
                    try:
                        self.driver.refresh()
                        self.wait_ready()
                        time.sleep(2)
                    except Exception:
                        pass
                    continue
                raise