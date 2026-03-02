import argparse
import sys
import time
import os

from engine.browser import create_driver
from steps.jpetstore_steps import JPetStoreSteps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="dev")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--username", default="j2ee")
    parser.add_argument("--password", default="j2ee")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--url", default="https://petstore.octoperf.com/")

    args = parser.parse_args()

    os.makedirs("artifacts", exist_ok=True)

    start_time = time.time()
    status = "FAIL"

    driver = create_driver(headless=args.headless, timeout_sec=args.timeout)

    try:
        steps = JPetStoreSteps(driver, timeout_sec=args.timeout)

        steps.open_site(args.url)
        steps.login(username=args.username, password=args.password)
        steps.buy_flow()

        status = "PASS"

    except Exception as e:
        try:
            driver.save_screenshot("artifacts/error.png")
        except Exception:
            pass
        print("Error:", e)

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    duration = round(time.time() - start_time, 2)
    generate_report(status, duration, args.env)

    print("=" * 50)
    print(f"FINAL STATUS: {status}")
    print("=" * 50)

    if status != "PASS":
        sys.exit(1)


def generate_report(status, duration, env):
    html = f"""
    <html>
    <body>
        <h2>Health Check Report</h2>
        <table border="1" cellpadding="10">
            <tr>
                <th>Environment</th>
                <th>Status</th>
                <th>Duration (sec)</th>
            </tr>
            <tr>
                <td>{env}</td>
                <td>{status}</td>
                <td>{duration}</td>
            </tr>
        </table>

        <p><b>Generated:</b> {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
    </body>
    </html>
    """

    with open("artifacts/health_report.html", "w") as f:
        f.write(html)

    print("Status:", status)
    print("Duration:", duration)


if __name__ == "__main__":
    main()