import json
import os
import time
import traceback
from datetime import datetime
import requests

from engine.browser import create_driver
from steps.jpetstore_steps import JPetStoreSteps


ARTIFACTS_DIR = "artifacts"
SCREENSHOT_DIR = os.path.join(ARTIFACTS_DIR, "screenshots")
HISTORY_FILE = os.path.join(ARTIFACTS_DIR, "history.jsonl")
LATEST_REPORT = os.path.join(ARTIFACTS_DIR, "health_report.html")
SUMMARY_REPORT = os.path.join(ARTIFACTS_DIR, "summary_report.html")


def _ensure_dirs():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def load_config(env_name: str):
    path = os.path.join("config", f"{env_name.lower()}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_latest_html(result: dict):
    status = result["status"]
    env_name = result["env_name"]
    duration = result["duration_sec"]
    ts = result["timestamp"]
    err = result.get("error", "")

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>MC Synthetic Monitoring - {env_name}</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 20px; }}
    .ok {{ color: #0a7b2c; font-weight: 700; }}
    .fail {{ color: #b00020; font-weight: 700; }}
    .box {{ padding: 14px; border: 1px solid #ddd; border-radius: 10px; }}
    pre {{ background: #f6f6f6; padding: 10px; border-radius: 8px; overflow: auto; }}
  </style>
</head>
<body>
  <h2>MC Synthetic Monitoring</h2>
  <div class="box">
    <div><b>Env:</b> {env_name}</div>
    <div><b>Status:</b> <span class="{ 'ok' if status=='PASS' else 'fail' }">{status}</span></div>
    <div><b>Duration:</b> {duration:.2f}s</div>
    <div><b>Timestamp:</b> {ts}</div>
  </div>
  <h3>Error (only if FAIL)</h3>
  <pre>{err}</pre>
</body>
</html>
"""
    with open(LATEST_REPORT, "w", encoding="utf-8") as f:
        f.write(html)


def append_history(result: dict):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


def generate_summary_table(max_rows: int = 50):
    rows = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except:
                    pass

    rows = rows[-max_rows:]

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    trs = ""
    for r in reversed(rows):
        cls = "ok" if r["status"] == "PASS" else "fail"
        trs += f"""
        <tr>
          <td>{esc(r["timestamp"])}</td>
          <td>{esc(r["env_name"])}</td>
          <td class="{cls}">{esc(r["status"])}</td>
          <td>{r["duration_sec"]:.2f}</td>
          <td><small>{esc((r.get("error") or "")[:200])}</small></td>
        </tr>
        """

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>MC Synthetic Monitoring - Summary</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; }}
    th {{ background: #f4f4f4; }}
    .ok {{ color: #0a7b2c; font-weight: 700; }}
    .fail {{ color: #b00020; font-weight: 700; }}
  </style>
</head>
<body>
  <h2>MC Synthetic Monitoring - Last {len(rows)} Runs</h2>
  <p>Latest report: <code>artifacts/health_report.html</code></p>
  <table>
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>Env</th>
        <th>Status</th>
        <th>Duration (s)</th>
        <th>Error (first 200 chars)</th>
      </tr>
    </thead>
    <tbody>
      {trs}
    </tbody>
  </table>
</body>
</html>
"""
    with open(SUMMARY_REPORT, "w", encoding="utf-8") as f:
        f.write(html)


def notify_slack(webhook_url: str, text: str):
    if not webhook_url:
        return
    requests.post(webhook_url, json={"text": text}, timeout=10)


def notify_teams(webhook_url: str, title: str, text: str):
    if not webhook_url:
        return
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title,
        "themeColor": "0076D7",
        "title": title,
        "text": text
    }
    requests.post(webhook_url, json=payload, timeout=10)


def main():
    _ensure_dirs()

    env_name = os.getenv("MC_ENV", "DEV").upper()
    cfg = load_config(env_name)

    # Override via env vars (for Jenkins)
    headless = os.getenv("MC_HEADLESS")
    if headless is not None:
        cfg["headless"] = headless.lower() in ("1", "true", "yes")

    username = os.getenv("MC_USERNAME", cfg["username"])
    password = os.getenv("MC_PASSWORD", cfg["password"])

    start = time.time()
    status = "PASS"
    err = ""
    screenshot_path = ""

    driver = None
    try:
        driver = create_driver(
            headless=cfg["headless"],
            page_load_timeout_sec=cfg["page_load_timeout_sec"],
            chromedriver_path=cfg["chromedriver_path"],
        )

        steps = JPetStoreSteps(driver, cfg["step_timeout_sec"])
        steps.open_site(cfg["base_url"])
        steps.login(username, password)
        steps.buy_flow()

    except Exception:
        status = "FAIL"
        err = traceback.format_exc()

        # screenshot on failure
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"{env_name}_{ts}.png")
            if driver:
                driver.save_screenshot(screenshot_path)
        except:
            pass

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

    duration = time.time() - start
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "env_name": env_name,
        "status": status,
        "duration_sec": duration,
        "error": err,
        "screenshot": screenshot_path
    }

    write_latest_html(result)
    append_history(result)
    generate_summary_table(max_rows=50)

    # Alerts
    notify_cfg = cfg.get("notify", {})
    slack_enabled = notify_cfg.get("slack_enabled", False)
    teams_enabled = notify_cfg.get("teams_enabled", False)
    email_enabled = notify_cfg.get("email_enabled", False)

    # We’ll let Jenkins handle Email (best practice).
    # But we can still push Slack/Teams from Python.
    if status == "FAIL":
        msg = f"❌ MC Synthetic FAIL ({env_name}) | {duration:.2f}s\nSee artifacts/health_report.html\n{(err[:400] + '...') if err else ''}"
        if slack_enabled:
            notify_slack(notify_cfg.get("slack_webhook_url", ""), msg)
        if teams_enabled:
            notify_teams(notify_cfg.get("teams_webhook_url", ""), f"MC Synthetic FAIL - {env_name}", msg)

    # Print final
    print(f"Status: {status}")
    print(f"Duration: {duration:.2f}s")
    print(f"Report: {LATEST_REPORT}")
    print(f"Summary: {SUMMARY_REPORT}")
    if screenshot_path:
        print(f"Screenshot: {screenshot_path}")

    # Non-zero exit on FAIL (so Jenkins marks build failed)
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()