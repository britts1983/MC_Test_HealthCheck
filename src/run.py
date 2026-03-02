import argparse
import os
import sys
import time
import traceback

from engine.browser import create_driver
from steps.jpetstore_steps import JPetStoreSteps


ARTIFACTS_DIR = "artifacts"
SCREENSHOTS_DIR = "artifacts/screenshots"


def ensure_dirs():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="dev")
    parser.add_argument("--headless", action="store_true")

    parser.add_argument("--username", default="j2ee")
    parser.add_argument("--password", default="j2ee")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--url", default="https://petstore.octoperf.com/")

    args = parser.parse_args()

    ensure_dirs()

    start_time = time.time()
    status = "FAIL"
    order_info = ""

    driver = create_driver(headless=args.headless, timeout_sec=args.timeout)

    try:
        steps = JPetStoreSteps(driver, timeout_sec=args.timeout, screenshots_dir=SCREENSHOTS_DIR)

        steps.open_site(args.url)
        steps.login(username=args.username, password=args.password)
        order_info = steps.buy_flow()

        status = "PASS"

    except Exception as e:
        # Try to capture last state (this also rotates automatically because it is same folder naming)
        try:
            ts = time.strftime("%Y%m%d_%H%M%S")
            driver.save_screenshot(f"{SCREENSHOTS_DIR}/{ts}_ERROR.png")
        except Exception:
            pass

        print("Error:", e)
        print("------ TRACEBACK ------")
        traceback.print_exc()
        print("-----------------------")

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    duration = round(time.time() - start_time, 2)
    generate_report(status, duration, args.env, order_info)

    print("==================================================")
    print(f"FINAL STATUS: {status}")
    print("==================================================")

    if status != "PASS":
        sys.exit(1)


def generate_report(status, duration, env, order_info):
    generated = time.strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <html>
    <body>
        <h2>Health Check Report</h2>
        <table border="1" cellpadding="10">
            <tr>
                <th>Environment</th>
                <th>Status</th>
                <th>Duration (sec)</th>
                <th>Order Proof</th>
            </tr>
            <tr>
                <td>{env}</td>
                <td>{status}</td>
                <td>{duration}</td>
                <td>{order_info or "N/A"}</td>
            </tr>
        </table>

        <p><b>Generated:</b> {generated}</p>
        <p><b>Screenshots folder:</b> {SCREENSHOTS_DIR}</p>
        <p>Latest 20 screenshots are kept (FIFO rotation).</p>
    </body>
    </html>
    """

    with open(f"{ARTIFACTS_DIR}/health_report.html", "w") as f:
        f.write(html)

    print("Status:", status)
    print("Duration:", duration)


if __name__ == "__main__":
    main()