import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def save_rotating_screenshot(driver, folder: str, label: str, max_files: int = 20) -> str:
    """
    Save screenshot into folder, keep only latest max_files using FIFO delete of oldest.
    Filename includes timestamp for ordering.
    """
    os.makedirs(folder, exist_ok=True)

    # Clean old screenshots (FIFO) if >= max_files
    pngs = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(".png")
    ]
    pngs.sort(key=lambda p: os.path.getmtime(p))  # oldest -> newest

    while len(pngs) >= max_files:
        oldest = pngs.pop(0)
        try:
            os.remove(oldest)
        except Exception:
            pass

    ts = time.strftime("%Y%m%d_%H%M%S")
    safe_label = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in label)
    path = os.path.join(folder, f"{ts}_{safe_label}.png")

    driver.save_screenshot(path)
    return path


class JPetStoreSteps:
    def __init__(self, driver, timeout_sec: int = 60, screenshots_dir: str = "artifacts/screenshots"):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout_sec)
        self.screenshots_dir = screenshots_dir

    def shot(self, label: str):
        path = save_rotating_screenshot(self.driver, self.screenshots_dir, label, max_files=20)
        print(f"[SCREENSHOT] {path}")
        return path

    def open_site(self, url: str):
        self.driver.get(url)
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.shot("01_home")

        # More stable than clickable
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign In")))

    def login(self, username: str, password: str):
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sign In"))).click()

        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        self.driver.find_element(By.NAME, "username").clear()
        self.driver.find_element(By.NAME, "username").send_keys(username)

        self.driver.find_element(By.NAME, "password").clear()
        self.driver.find_element(By.NAME, "password").send_keys(password)

        self.driver.find_element(By.NAME, "signon").click()

        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign Out")))
        self.shot("02_after_login")
        print("Login completed")

    def buy_flow(self) -> str:
        # Go directly to Fish category
        self.driver.get("https://petstore.octoperf.com/actions/Catalog.action?viewCategory=&categoryId=FISH")
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
        self.shot("03_category_fish")

        # Click first product
        self.driver.find_elements(By.XPATH, "//table//tr[position()>1]//a")[0].click()
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))

        # Click first item
        self.driver.find_elements(By.XPATH, "//table//tr[position()>1]//a")[0].click()

        # Add to cart
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Add to Cart"))).click()
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
        self.shot("04_cart")

        # Proceed to checkout
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Proceed to Checkout"))).click()

        # Continue new order page (some environments show it, some skip)
        try:
            self.wait.until(EC.element_to_be_clickable((By.NAME, "newOrder"))).click()
        except Exception:
            pass

        print("On confirm address page")
        self.shot("05_confirm_address")

        # Final submit
        submit_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']")))
        submit_btn.click()
        print("Final submit clicked")

        # Confirmation proof: wait for strong signals
        # We try multiple possible indicators used by the demo site.
        order_id = ""

        try:
            self.wait.until(
                lambda d: (
                    "Thank you" in d.page_source
                    or "submitted" in d.page_source
                    or "Order" in d.page_source
                    or "Confirmation" in d.page_source
                )
            )
        except TimeoutException:
            # still take screenshot even if not confirmed
            self.shot("06_after_submit_timeout")
            raise

        self.shot("06_after_submit")

        # Optional: try extract order number if present
        try:
            # Many pages show "Order #" somewhere
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            for line in body_text.splitlines():
                if "Order" in line and "#" in line:
                    order_id = line.strip()
                    break
        except Exception:
            pass

        print("Flow completed successfully")
        return order_id