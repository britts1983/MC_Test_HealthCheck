import os
from datetime import datetime

def write_html(artifacts_dir, env_name, status, duration, error):
    os.makedirs(artifacts_dir, exist_ok=True)
    path = os.path.join(artifacts_dir, "health_report.html")
    with open(path, "w") as f:
        f.write(f"""
        <html>
        <body>
        <h2>MC Synthetic Monitoring</h2>
        <p><b>Env:</b> {env_name}</p>
        <p><b>Status:</b> {status}</p>
        <p><b>Duration:</b> {duration:.2f}s</p>
        <p><b>Error:</b> {error}</p>
        <p><b>Timestamp:</b> {datetime.now()}</p>
        </body>
        </html>
        """)
    return path
