import argparse
import os
import time
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from steps.jpetstore_steps import JPetStoreSteps


# -------------------------------------------------
# HTML REPORT GENERATOR
# -------------------------------------------------
def generate_report(env, status, duration, order_proof):
    html = f"""
    <html>
    <head>
        <title>Health Check Report</title>
        <style>
            body {{ font-family: Arial; background:#f5f5f5; }}
            table {{ border-collapse: collapse; width: 60%; margin: 20px auto; background:white; }}
            th, td {{ border:1px solid #ccc; padding:10px; text-align:center; }}
            th {{ background:#333; color:white; }}
            .pass {{ color:green; font-weight:bold; }}
            .fail {{ color:red; font-weight:bold; }}
        </style>
    </head>
    <body>
        <h2 style="text-align:center;">JPetStore Health Check Report</h2>
        <table>
            <tr>
                <th>Environment</th>
                <th>Status</th>
                <th>Duration (sec)</th>
                <th>Order Proof</th>
            </tr>
            <tr>
                <td>{env}</td>
                <td class="{'pass' if status=='PASS' else 'fail'}">{status}</td>
                <td>{round(duration,2)}</td>
                <td>{order_proof}</td>
            </tr>
        </table>
        <p style="text-align:center;">Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p style="text-align:center;">Screenshots folder: artifacts/screenshots</p>
        <p style="text-align:center;">Latest 20 screenshots are kept (FIFO rotation).</p>
    </body>
    </html>
    """

    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/health_report.html", "w", encoding="utf-8") as f:
        f.write(html)


# -------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--url", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    start_time = time.time()
    final_status = "FAIL"
    order_info = "N/A"

    driver = None

    try:
        # Chrome options
        chrome_options = Options()
        if args.headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        driver.set_page_load_timeout(args.timeout)

        steps = JPetStoreSteps(
            driver,
            timeout_sec=args.timeout,
            screenshots_dir="artifacts/screenshots"
        )

        steps.open_site(args.url)
        steps.login(args.username, args.password)
        order_info = steps.buy_flow()

        final_status = "PASS"

    except Exception as e:
        print("Error:", str(e))
        print("------ TRACEBACK ------")
        traceback.print_exc()
        print("-----------------------")

    finally:
        if driver:
            driver.quit()

    duration = time.time() - start_time

    print("Status:", final_status)
    print("Duration:", round(duration, 2))
    print("FINAL STATUS:", final_status)

    # Always generate report (even on failure)
    generate_report(args.env, final_status, duration, order_info)


if __name__ == "__main__":
    main()