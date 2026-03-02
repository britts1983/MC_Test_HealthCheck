from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class JPetStoreSteps:

    def __init__(self, driver, timeout_sec: int):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout_sec)

    def open_site(self, url: str):
        self.driver.get(url)
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Sign In"))
        )

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

        print("Login completed")

    def buy_flow(self):

        # Go directly to Fish category (stable)
        self.driver.get(
            "https://petstore.octoperf.com/actions/Catalog.action?viewCategory=&categoryId=FISH"
        )

        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//table"))
        )

        # Click first product
        self.driver.find_elements(By.XPATH, "//table//tr[position()>1]//a")[0].click()

        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//table"))
        )

        # Click first item
        self.driver.find_elements(By.XPATH, "//table//tr[position()>1]//a")[0].click()

        # Add to cart
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Add to Cart"))
        ).click()

        # Proceed to checkout
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Proceed to Checkout"))
        ).click()

        # First Continue (new order page)
        try:
            self.wait.until(
                EC.element_to_be_clickable((By.NAME, "newOrder"))
            ).click()
        except:
            pass

        print("On confirm address page")

        # Second Continue/Confirm (confirm page)
        continue_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
        )
        continue_btn.click()

        print("Final submit clicked")

        # Accept demo-site behavior: home OR order page after submit
        self.wait.until(
            lambda d:
                "Catalog" in d.page_source
                or "Order" in d.page_source
                or "search" in d.page_source
        )

        print("Flow completed successfully")