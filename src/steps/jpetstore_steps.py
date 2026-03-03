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

    
    # Open site from jenkins Parameter
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


    # Login goes here
    def login(self, username, password):
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Sign In"))
        ).click()

        self.wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )

        u = self.driver.find_element(By.NAME, "username")
        p = self.driver.find_element(By.NAME, "password")

        u.clear()
        p.clear()
        u.send_keys(username)
        p.send_keys(password)

        self.driver.find_element(By.NAME, "signon").click()

        self.wait.until(
            EC.presence_of_element_located((By.LINK_TEXT, "Sign Out"))
        )

        self.wait_ready()
        save_screenshot(self.driver, self.screenshot_dir, "03_after_login")
        print("Login successful")

    
    # Buy section is here
    def buy_flow(self):
        try:
            # Go to Fish category
            self.driver.get(
                "https://petstore.octoperf.com/actions/Catalog.action?viewCategory=&categoryId=FISH"
            )
            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "04_fish_category")

            # Go to product section
            self.driver.get(
                "https://petstore.octoperf.com/actions/Catalog.action?viewProduct=&productId=FI-SW-01"
            )
            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "05_product_page")

            # Direct add-to-cart URL
            self.driver.get(
                "https://petstore.octoperf.com/actions/Cart.action?addItemToCart=&workingItemId=EST-1"
            )

            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "06_cart")

            # Goto checkout page
            self.driver.get(
                "https://petstore.octoperf.com/actions/Order.action?newOrderForm="
            )

            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "07_checkout_page")

            # Continue order (if required)
            try:
                continue_btn = self.wait.until(
                    EC.element_to_be_clickable((By.NAME, "newOrder"))
                )
                continue_btn.click()
            except:
                pass

            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "08_after_continue")

            # Final submit
            submit_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
            )
            submit_btn.click()

            # Wait for order confirmation
            self.wait.until(
                lambda d: "viewOrder" in d.current_url or "Order" in d.current_url
            )

            time.sleep(2)
            save_screenshot(self.driver, self.screenshot_dir, "09_success")

            print("Purchase completed successfully")
            return "Order placed successfully"

        except Exception:
            save_screenshot(self.driver, self.screenshot_dir, "99_failure")
            self.dump_page()
            raise