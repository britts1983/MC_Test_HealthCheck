import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
    # FINAL STABLE BUY FLOW WITH ORDER ID EXTRACTION
    # -------------------------------------------------
    def buy_flow(self):
        try:
            # Go to Fish category
            self.driver.get(
                "https://petstore.octoperf.com/actions/Catalog.action?viewCategory=&categoryId=FISH"
            )
            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "04_fish_category")

            # Go to product
            self.driver.get(
                "https://petstore.octoperf.com/actions/Catalog.action?viewProduct=&productId=FI-SW-01"
            )
            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "05_product_page")

            # Add to cart directly
            self.driver.get(
                "https://petstore.octoperf.com/actions/Cart.action?addItemToCart=&workingItemId=EST-1"
            )
            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "06_cart")

            # Go to checkout
            self.driver.get(
                "https://petstore.octoperf.com/actions/Order.action?newOrderForm="
            )
            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "07_checkout_page")

            # Click Continue (if present)
            try:
                continue_btn = self.wait.until(
                    EC.element_to_be_clickable((By.NAME, "newOrder"))
                )
                continue_btn.click()
            except:
                pass

            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "08_after_continue")

            # 🔥 FINAL CONFIRM BUTTON
            confirm_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Confirm']"))
            )
            confirm_button.click()

            # Wait for actual order confirmation
            self.wait.until(
                lambda d: "viewOrder" in d.current_url and "orderId=" in d.current_url
            )

            time.sleep(2)

            current_url = self.driver.current_url
            order_id = current_url.split("orderId=")[-1]

            save_screenshot(self.driver, self.screenshot_dir, "09_success")

            print("Order ID:", order_id)
            print("Purchase completed successfully")

            return f"Order ID: {order_id}"

        except Exception as e:
            save_screenshot(self.driver, self.screenshot_dir, "99_failure")
            self.dump_page()
            raise e