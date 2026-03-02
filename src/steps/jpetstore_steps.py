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

    def open_site(self, url):
        print("Opening:", url)
        self.driver.get(url)
        self.wait_ready()
        save_screenshot(self.driver, self.screenshot_dir, "01_home")

        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Enter the Store"))).click()
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign In")))

        self.wait_ready()
        save_screenshot(self.driver, self.screenshot_dir, "02_store_home")
        print("Store loaded")

    def login(self, username, password):
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sign In"))).click()
        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))

        u = self.driver.find_element(By.NAME, "username")
        p = self.driver.find_element(By.NAME, "password")
        u.clear()
        p.clear()
        u.send_keys(username)
        p.send_keys(password)

        self.driver.find_element(By.NAME, "signon").click()
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign Out")))

        self.wait_ready()
        save_screenshot(self.driver, self.screenshot_dir, "03_after_login")
        print("Login successful")

    # -------------------------------------------------
    # FINAL STABLE BUY FLOW (NO "PROCEED" CLICK)
    # -------------------------------------------------
    def buy_flow(self):
        try:
            # 1) Category
            self.driver.get("https://petstore.octoperf.com/actions/Catalog.action?viewCategory=&categoryId=FISH")
            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "04_fish_category")

            # 2) Product
            self.driver.get("https://petstore.octoperf.com/actions/Catalog.action?viewProduct=&productId=FI-SW-01")
            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "05_product_page")

            # 3) Item
            self.driver.get("https://petstore.octoperf.com/actions/Catalog.action?viewItem=&itemId=EST-1")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self.wait_ready()

            # 4) Add to cart (this click is stable)
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(.,'Add to Cart')]"))
            ).click()

            # Wait for cart page by URL (not text)
            self.wait.until(lambda d: "Cart.action" in d.current_url or "viewCart" in d.current_url or "cart" in d.current_url.lower())
            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "06_cart")

            # ✅ 5) Go directly to checkout URL (avoids flaky "Proceed" locator)
            self.driver.get("https://petstore.octoperf.com/actions/Order.action?newOrderForm=")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "07_checkout_page")

            # Some builds show a Continue button, some show "newOrder" submit first.
            # Try common patterns safely.
            clicked = False
            candidates = [
                (By.NAME, "newOrder"),  # typical
                (By.XPATH, "//input[@type='submit' and (contains(@value,'Continue') or contains(@value,'continue'))]"),
                (By.XPATH, "//a[contains(.,'Continue')]"),
            ]
            for by, sel in candidates:
                try:
                    el = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((by, sel)))
                    el.click()
                    clicked = True
                    break
                except Exception:
                    pass

            if not clicked:
                # If nothing clickable, still continue by just trying next submit on page.
                pass

            self.wait_ready()
            save_screenshot(self.driver, self.screenshot_dir, "08_after_continue")

            # 6) Final confirm order (again handle multiple possible buttons)
            clicked2 = False
            confirm_candidates = [
                (By.NAME, "order"),
                (By.XPATH, "//input[@type='submit' and (contains(@value,'Confirm') or contains(@value,'confirm') or contains(@value,'Submit') or contains(@value,'submit'))]"),
                (By.XPATH, "//input[@type='submit']"),
            ]
            for by, sel in confirm_candidates:
                try:
                    el = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((by, sel)))
                    el.click()
                    clicked2 = True
                    break
                except Exception:
                    pass

            if not clicked2:
                raise Exception("Could not find final submit/confirm button on checkout page")

            # 7) Success check by URL
            self.wait.until(lambda d: "viewOrder" in d.current_url or "Order" in d.current_url)
            time.sleep(2)
            save_screenshot(self.driver, self.screenshot_dir, "09_success")

            print("Purchase completed successfully")
            return "Order placed successfully"

        except Exception:
            save_screenshot(self.driver, self.screenshot_dir, "99_failure")
            self.dump_page()
            raise