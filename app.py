from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from tracker import TimeTracker

tracker = TimeTracker("mytime.yml")


class MyTimeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        message = query.get("msg", [""])[0]

        data = tracker.load_data()
        activities = sorted(data["activities"])
        running = data["running"]

        options = "".join(f'<option value="{a}">{a}</option>' for a in activities)
        running_text = (
            f"Running: {running['activity']} (started {running['start']})" if running else "No activity running"
        )

        html = f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>MyTime Tracker</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; max-width: 720px; }}
    .box {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }}
    .msg {{ color: #0a7; font-weight: 600; }}
    form {{ display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }}
    input, select, button {{ padding: 0.4rem; }}
  </style>
</head>
<body>
  <h1>MyTime Tracker</h1>
  <p class=\"msg\">{message}</p>

  <div class=\"box\">
    <h2>Activities</h2>
    <form method=\"post\" action=\"/add\">
      <input name=\"name\" placeholder=\"New activity\" required />
      <button type=\"submit\">Add</button>
    </form>
    <p>Available: {', '.join(activities) if activities else 'None yet'}</p>
  </div>

  <div class=\"box\">
    <h2>Tracking</h2>
    <p>{running_text}</p>
    <form method=\"post\" action=\"/start\">
      <select name=\"activity\" required>
        {options}
      </select>
      <button type=\"submit\">Start</button>
    </form>
    <form method=\"post\" action=\"/stop\">
      <button type=\"submit\">Stop</button>
    </form>
  </div>

  <div class=\"box\">
    <h2>Export Monthly CSV</h2>
    <form method=\"post\" action=\"/export\">
      <input type=\"month\" name=\"month\" required />
      <button type=\"submit\">Export</button>
    </form>
  </div>
</body>
</html>
"""

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        form = parse_qs(body)

        try:
            if self.path == "/add":
                tracker.add_activity(form.get("name", [""])[0])
                self._redirect("Activity added")
                return

            if self.path == "/start":
                tracker.start_activity(form.get("activity", [""])[0])
                self._redirect("Tracking started")
                return

            if self.path == "/stop":
                entry = tracker.stop_activity()
                self._redirect(f"Stopped {entry['activity']} ({entry['duration_seconds']}s)")
                return

            if self.path == "/export":
                month_value = form.get("month", [""])[0]
                year_str, month_str = month_value.split("-")
                year, month = int(year_str), int(month_str)
                report_path = Path("reports") / f"report-{year:04d}-{month:02d}.csv"
                count = tracker.export_monthly_csv(year, month, report_path)
                self._redirect(f"Exported {count} entries to {report_path}")
                return

            self.send_error(404, "Unknown endpoint")
        except Exception as exc:
            self._redirect(f"Error: {exc}")

    def log_message(self, format: str, *args: object) -> None:
        return

    def _redirect(self, message: str) -> None:
        self.send_response(303)
        self.send_header("Location", f"/?{urlencode({'msg': message})}")
        self.end_headers()


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = HTTPServer((host, port), MyTimeHandler)
    print(f"MyTime running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
