import argparse
import time
from engine.browser import create_driver
from steps.jpetstore_steps import JPetStoreSteps

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="dev")
    parser.add_argument("--headless", action="store_true")

    args = parser.parse_args()

    start_time = time.time()

    driver = create_driver(headless=args.headless, timeout_sec=60)

    try:
        steps = JPetStoreSteps(driver)

        steps.login()
        steps.buy_flow()

        status = "PASS"

    except Exception as e:
        driver.save_screenshot("artifacts/error.png")
        status = "FAIL"
        print("Error:", e)

    finally:
        driver.quit()

    duration = round(time.time() - start_time, 2)

    generate_report(status, duration, args.env)


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
    </body>
    </html>
    """

    with open("artifacts/health_report.html", "w") as f:
        f.write(html)

    print("Status:", status)
    print("Duration:", duration)