"""
Flask-based version of the MyTime Tracker web application.
This version provides the same endpoints and HTML as the BaseHTTPRequestHandler version,
but uses Flask for routing and rendering.
"""
from flask import Flask, render_template_string, request, redirect, url_for
from pathlib import Path
from tracker import TimeTracker

app = Flask(__name__)
tracker = TimeTracker("mytime.yml")

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>MyTime Tracker</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; max-width: 720px; }
    .box { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    .msg { color: #0a7; font-weight: 600; }
    form { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
    input, select, button { padding: 0.4rem; }
  </style>
</head>
<body>
  <h1>MyTime Tracker</h1>
  <p class="msg">{{ message }}</p>

  <div class="box">
    <h2>Activities</h2>
    <form method="post" action="{{ url_for('add') }}">
      <input name="name" placeholder="New activity" required />
      <button type="submit">Add</button>
    </form>
    <p>Available: {{ activities|join(', ') if activities else 'None yet' }}</p>
  </div>

  <div class="box">
    <h2>Tracking</h2>
    <p>{{ running_text }}</p>
    <form method="post" action="{{ url_for('start') }}">
      <select name="activity" required>
        {% for a in activities %}<option value="{{ a }}">{{ a }}</option>{% endfor %}
      </select>
      <button type="submit">Start</button>
    </form>
    <form method="post" action="{{ url_for('stop') }}">
      <button type="submit">Stop</button>
    </form>
  </div>

  <div class="box">
    <h2>Export Monthly CSV</h2>
    <form method="post" action="{{ url_for('export') }}">
      <input type="month" name="month" required />
      <button type="submit">Export</button>
    </form>
  </div>
</body>
</html>
"""


def get_context(message=""):
    """Get the context data for rendering the HTML template."""
    data = tracker.load_data()
    activities = sorted(data["activities"])
    running = data["running"]
    if running:
        running_text = f"Running: {running['activity']} (started {running['start']})"
    else:
        running_text = "No activity running"
    return dict(
        message=message,
        activities=activities,
        running_text=running_text,
    )

@app.route("/", methods=["GET"])
def index():
    """Render the main page with the current activities and tracking status."""
    return render_template_string(HTML_TEMPLATE, **get_context(request.args.get("msg", "")))

@app.route("/add", methods=["POST"])
def add():
    """Handle adding a new activity and redirect back to the main page with a status message."""
    try:
        tracker.add_activity(request.form.get("name", ""))
        return redirect(url_for("index", msg="Activity added"))
    except (ValueError, KeyError) as exc:
        return redirect(url_for("index", msg=f"Error: {exc}"))

@app.route("/start", methods=["POST"])
def start():
    """Handle starting an activity and redirect back to the main page with a status message."""
    try:
        tracker.start_activity(request.form.get("activity", ""))
        return redirect(url_for("index", msg="Tracking started"))
    except (ValueError, KeyError) as exc:
        return redirect(url_for("index", msg=f"Error: {exc}"))

@app.route("/stop", methods=["POST"])
def stop():
    """Handle stopping the current activity and 
    redirect back to the main page with a status message."""
    try:
        entry = tracker.stop_activity()
        return redirect(url_for("index",
                                msg=f"Stopped {entry['activity']} ({entry['duration_seconds']}s)"))
    except (ValueError, KeyError) as exc:
        return redirect(url_for("index", msg=f"Error: {exc}"))

@app.route("/export", methods=["POST"])
def export():
    """Handle exporting the monthly CSV report and 
    redirect back to the main page with a status message."""
    try:
        month_value = request.form.get("month", "")
        year_str, month_str = month_value.split("-")
        year, month = int(year_str), int(month_str)
        report_path = Path("reports") / f"report-{year:04d}-{month:02d}.csv"
        count = tracker.export_monthly_csv(year, month, report_path)
        return redirect(url_for("index", msg=f"Exported {count} entries to {report_path}"))
    except (ValueError, KeyError) as exc:
        return redirect(url_for("index", msg=f"Error: {exc}"))

if __name__ == "__main__":
    app.run(debug=True)
