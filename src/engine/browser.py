from selenium import webdriver


def create_driver(headless: bool, timeout_sec: int):
    options = webdriver.ChromeOptions()

    options.add_argument("--incognito")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # IMPORTANT for some CI/mac environments
    options.add_argument("--remote-debugging-port=9222")

    if headless:
        options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    driver.set_page_load_timeout(timeout_sec)
    driver.set_script_timeout(timeout_sec)

    return driver