import os
import time
from typing import List, Tuple, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException


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

    def _scroll_into_view(self, el):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.3)
        except Exception:
            pass

    def _safe_click(self, locators: List[Tuple[str, str]], label_on_fail: str) -> None:
        """
        Try multiple locators; scroll into view; click; fallback to JS click.
        """
        last_err: Optional[Exception] = None

        for by, value in locators:
            try:
                el = self.wait.until(EC.presence_of_element_located((by, value)))
                self._scroll_into_view(el)

                try:
                    self.wait.until(EC.element_to_be_clickable((by, value)))
                    el.click()
                    return
                except (ElementClickInterceptedException, TimeoutException):
                    # fallback JS click
                    self.driver.execute_script("arguments[0].click();", el)
                    return

            except Exception as e:
                last_err = e
                continue

        # If all locators fail
        self.shot(label_on_fail)
        self.dump_page()
        raise TimeoutException(f"Could not click element using locators: {locators}. Last error: {last_err}")

    # -------------------------------
    # OPEN SITE (REAL USER FLOW)
    # -------------------------------
    def open_site(self, url: str):
        print("Opening:", url)
        self.driver.get(url)
        self.wait_ready()
        self.shot("01_home")

        # Click "Enter the Store"
        self._safe_click(
            locators=[
                (By.LINK_TEXT, "Enter the Store"),
                (By.PARTIAL_LINK_TEXT, "Enter"),
                (By.CSS_SELECTOR, "a[href*='Catalog.action']"),
            ],
            label_on_fail="01_enter_store_not_found",
        )

        # Wait until store home is ready (Sign In should exist)
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign In")))
        self.wait_ready()
        self.shot("02_store_home")
        print("Store loaded")

    # -------------------------------
    # LOGIN
    # -------------------------------
    def login(self, username: str, password: str):
        self._safe_click(
            locators=[
                (By.LINK_TEXT, "Sign In"),
                (By.PARTIAL_LINK_TEXT, "Sign In"),
                (By.CSS_SELECTOR, "a[href*='signonForm']"),
            ],
            label_on_fail="02_signin_not_found",
        )

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
        IMPORTANT FIX:
        - JPetStore category links (FISH, DOGS...) are image links -> link text is EMPTY.
        - So we must click by href containing categoryId=FISH.
        """
        for attempt in range(1, 3):
            try:
                if not self.is_logged_in():
                    raise TimeoutException("Not logged in (Sign Out not found).")

                # Click FISH category (image link) using href match
                self._safe_click(
                    locators=[
                        (By.CSS_SELECTOR, "a[href*='categoryId=FISH']"),
                        (By.XPATH, "//a[contains(@href,'categoryId=FISH')]"),
                        (By.XPATH, "//div[@id='SidebarContent']//a[contains(@href,'FISH')]"),
                    ],
                    label_on_fail=f"04_fish_link_not_found_attempt_{attempt}",
                )

                # Wait product list links appear
                self.wait.until(
                    lambda d: len(d.find_elements(By.XPATH, "//a[contains(@href,'Product.action')]")) > 0
                )
                self.wait_ready()
                self.shot("04_fish_category")

                # Click first product
                products = self.driver.find_elements(By.XPATH, "//a[contains(@href,'Product.action')]")
                if not products:
                    raise TimeoutException("No Product.action links found on category page.")
                self._scroll_into_view(products[0])
                products[0].click()

                # Wait item list links appear
                self.wait.until(
                    lambda d: len(d.find_elements(By.XPATH, "//a[contains(@href,'Item.action')]")) > 0
                )
                self.wait_ready()
                self.shot("05_product_page")

                # Click first item
                items = self.driver.find_elements(By.XPATH, "//a[contains(@href,'Item.action')]")
                if not items:
                    raise TimeoutException("No Item.action links found on product page.")
                self._scroll_into_view(items[0])
                items[0].click()

                # Add to cart
                self._safe_click(
                    locators=[
                        (By.LINK_TEXT, "Add to Cart"),
                        (By.PARTIAL_LINK_TEXT, "Add to Cart"),
                        (By.XPATH, "//a[contains(@href,'addItemToCart')]"),
                    ],
                    label_on_fail="06_add_to_cart_not_found",
                )
                self.wait_ready()
                self.shot("06_cart")

                # Proceed to checkout
                self._safe_click(
                    locators=[
                        (By.LINK_TEXT, "Proceed to Checkout"),
                        (By.PARTIAL_LINK_TEXT, "Proceed"),
                        (By.XPATH, "//a[contains(@href,'newOrderForm')]"),
                    ],
                    label_on_fail="07_checkout_button_not_found",
                )

                # Sometimes there is an intermediate "newOrder" button
                try:
                    btn = self.wait.until(EC.presence_of_element_located((By.NAME, "newOrder")))
                    self._scroll_into_view(btn)
                    try:
                        btn.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    pass

                self.wait_ready()
                self.shot("07_checkout")

                # Final submit
                submit = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='submit']")))
                self._scroll_into_view(submit)
                try:
                    submit.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", submit)

                # Confirmation
                self.wait.until(lambda d: ("Thank you" in d.page_source) or ("Order" in d.page_source))
                self.wait_ready()
                self.shot("08_success")

                print("Purchase completed successfully")
                return "Order placed successfully"

            except Exception as e:
                print(f"[BUY_FLOW] Attempt {attempt} failed: {e}")
                self.shot(f"99_buyflow_fail_attempt_{attempt}")
                self.dump_page()

                if attempt < 2:
                    try:
                        self.driver.refresh()
                        self.wait_ready()
                        time.sleep(2)
                    except Exception:
                        pass
                    continue
                raise