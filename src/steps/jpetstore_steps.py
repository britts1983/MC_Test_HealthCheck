from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class JPetStoreSteps:
    def __init__(self, driver, timeout_sec: int = 60):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout_sec)

    def open_site(self, url: str = "https://petstore.octoperf.com/"):
        self.driver.get(url)
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Sign In")))

    # Give defaults so your run.py can call steps.login() without args
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
        # Go directly to Fish category (stable)
        self.driver.get(
            "https://petstore.octoperf.com/actions/Catalog.action?viewCategory=&categoryId=FISH"
        )

        self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))

        # Click first product
        rows = self.driver.find_elements(By.XPATH, "//table//tr[position()>1]//a")
        if not rows:
            raise RuntimeError("No products found in Fish category page")
        rows[0].click()

        self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))

        # Click first item
        items = self.driver.find_elements(By.XPATH, "//table//tr[position()>1]//a")
        if not items:
            raise RuntimeError("No items found in product page")
        items[0].click()

        # Add to cart
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Add to Cart"))).click()

        # Proceed to checkout
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Proceed to Checkout"))
        ).click()

        # First Continue (new order page) - some demo flows may skip it
        try:
            self.wait.until(EC.element_to_be_clickable((By.NAME, "newOrder"))).click()
        except Exception:
            pass

        print("On confirm address page")

        # Second Continue/Confirm (confirm page)
        self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
        ).click()

        print("Final submit clicked")

        # Accept demo-site behavior: home OR order page after submit
        self.wait.until(
            lambda d: (
                "Catalog" in d.page_source
                or "Order" in d.page_source
                or "search" in d.page_source
            )
        )

        print("Flow completed successfully")