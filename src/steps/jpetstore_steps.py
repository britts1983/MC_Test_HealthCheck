import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class JPetStoreSteps:
    def __init__(self, driver, timeout_sec: int = 120):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout_sec)
        self.timeout_sec = timeout_sec

    def open_site(self, url: str = "https://petstore.octoperf.com/"):
        # Retry once because the demo site sometimes loads slow
        for attempt in range(1, 3):
            try:
                self.driver.get(url)

                # Wait for DOM to be ready
                self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

                # Wait for Sign In to be present (presence is safer than clickable)
                self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign In")))
                return

            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(3)  # small pause before retry

    def login(self, username: str = "j2ee", password: str = "j2ee"):
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sign In"))).click()

        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))

        user_el = self.driver.find_element(By.NAME, "username")
        user_el.clear()
        user_el.send_keys(username)

        pass_el = self.driver.find_element(By.NAME, "password")
        pass_el.clear()
        pass_el.send_keys(password)

        self.driver.find_element(By.NAME, "signon").click()

        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign Out")))
        print("Login completed")

    def buy_flow(self):
        self.driver.get(
            "https://petstore.octoperf.com/actions/Catalog.action?viewCategory=&categoryId=FISH"
        )

        self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))

        rows = self.driver.find_elements(By.XPATH, "//table//tr[position()>1]//a")
        if not rows:
            raise RuntimeError("No products found in Fish category page")
        rows[0].click()

        self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))

        items = self.driver.find_elements(By.XPATH, "//table//tr[position()>1]//a")
        if not items:
            raise RuntimeError("No items found in product page")
        items[0].click()

        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Add to Cart"))).click()

        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Proceed to Checkout"))).click()

        try:
            self.wait.until(EC.element_to_be_clickable((By.NAME, "newOrder"))).click()
        except Exception:
            pass

        print("On confirm address page")

        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))).click()

        print("Final submit clicked")

        self.wait.until(
            lambda d: (
                "Catalog" in d.page_source
                or "Order" in d.page_source
                or "search" in d.page_source
            )
        )

        print("Flow completed successfully")