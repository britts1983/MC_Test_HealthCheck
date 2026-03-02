import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def save_screenshot(driver, folder, label):
    os.makedirs(folder, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, f"{ts}_{label}.png")
    driver.save_screenshot(path)
    print(f"[SCREENSHOT] {path}")
    return path


class JPetStoreSteps:

    def __init__(self, driver, timeout_sec=120, screenshots_dir="artifacts/screenshots"):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout_sec)
        self.screenshot_dir = screenshots_dir

    def wait_ready(self):
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(1)

    def dump_page(self):
        os.makedirs("artifacts", exist_ok=True)
        with open("artifacts/debug_page.html", "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

    # -------------------------------------------------
    # OPEN SITE
    # -------------------------------------------------
    def open_site(self, url):
        print("Opening:", url)
        self.driver.get(url)
        self.wait_ready()
        save_screenshot(self.driver, self.screenshot_dir, "01_home")

        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Enter the Store"))
        ).click()

        self.wait.until(
            EC.presence_of_element_located((By.LINK_TEXT, "Sign In"))
        )

        self.wait_ready()
        save_screenshot(self.driver, self.screenshot_dir, "02_store_home")
        print("Store loaded")

    # -------------------------------------------------
    # LOGIN
    # -------------------------------------------------
    def login(self, username, password):
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

        self.wait_ready()
        save_screenshot(self.driver, self.screenshot_dir, "03_after_login")
        print("Login successful")

    # -------------------------------------------------
    # BUY FLOW (STABLE VERSION)
    # -------------------------------------------------
    def buy_flow(self):
        try:
            # Click FISH category
            self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a[href*='categoryId=FISH']")
                )
            ).click()

            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "04_fish_category")

            # Click first product using productId
            product = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(@href,'productId=')]")
                )
            )
            product.click()

            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "05_product_page")

            # Click first item using itemId
            item = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(@href,'itemId=')]")
                )
            )
            item.click()

            self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(),'Add to Cart')]")
                )
            ).click()

            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "06_cart")

            # Checkout
            self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(),'Proceed')]")
                )
            ).click()

            try:
                self.wait.until(
                    EC.element_to_be_clickable((By.NAME, "newOrder"))
                ).click()
            except:
                pass

            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "07_checkout")

            # Final submit
            self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit']")
                )
            ).click()

            self.wait.until(
                lambda d: "Order" in d.page_source or "Thank you" in d.page_source
            )

            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "08_success")

            print("Purchase completed successfully")
            return "Order placed successfully"

        except Exception as e:
            save_screenshot(self.driver, self.screenshot_dir, "99_failure")
            self.dump_page()
            raise