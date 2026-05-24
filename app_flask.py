"""
Flask-based version of the MyTime Tracker web application.
This version provides the same endpoints and HTML as the BaseHTTPRequestHandler version,
but uses Flask for routing and rendering.
"""
from pathlib import Path
from flask import Flask, render_template_string, request, redirect, url_for
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
    .activity-btns { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }
    .activity-btn {
      border: none;
      color: #fff;
      padding: 0.5rem 1.2rem;
      border-radius: 5px;
      font-size: 1rem;
      cursor: pointer;
      margin-bottom: 0.5rem;
    }
    .activity-running { background: #2196f3; }
    .activity-idle { background: #43a047; }
    table { border-collapse: collapse; margin-top: 1rem; }
    th, td { border: 1px solid #bbb; padding: 0.4rem 0.8rem; text-align: left; }
    th { background: #f0f0f0; }
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
    <div class="activity-btns">
      {% for a in activities %}
        <form method="post" action="{{ url_for('toggle_activity') }}" style="display:inline;">
          <input type="hidden" name="activity" value="{{ a }}" />
          <button type="submit" class="activity-btn {% if running_activity == a %}activity-running{% else %}activity-idle{% endif %}">
            {{ a }}
          </button>
        </form>
      {% endfor %}
    </div>
  </div>

  <div class="box">
    <h2>Export Monthly CSV</h2>
    <form method="post" action="{{ url_for('export') }}">
      <input type="month" name="month" required />
      <button type="submit">Export</button>
    </form>
    {% if summary_table %}
      <h3>Monthly Summary</h3>
      <table>
        <tr><th>Activity</th><th>Total Seconds</th><th>Total Hours</th></tr>
        {% for row in summary_table %}
        <tr>
          <td>{{ row['activity'] }}</td>
          <td>{{ row['total_seconds'] }}</td>
          <td>{{ row['total_hours'] }}</td>
        </tr>
        {% endfor %}
      </table>
      <p><a href="{{ detailed_csv_url }}" download>Download detailed CSV report</a></p>
    {% endif %}
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
        running_activity = running['activity']
    else:
        running_text = "No activity running"
        running_activity = None
    return {
        "message": message,
        "activities": activities,
        "running_text": running_text,
        "running_activity": running_activity,
    }

@app.route("/toggle_activity", methods=["POST"])
def toggle_activity():
    """Toggle activity: if running, stop; if not, start. If another is running, switch."""
    activity = request.form.get("activity", "")
    data = tracker.load_data()
    running = data["running"]
    msg = ""
    try:
        if running and running["activity"] == activity:
            entry = tracker.stop_activity()
            msg = f"Stopped {entry['activity']} ({entry['duration_seconds']}s)"
        elif running and running["activity"] != activity:
            entry = tracker.stop_activity()
            tracker.start_activity(activity)
            msg = f"Switched from {entry['activity']} to {activity}"
        else:
            tracker.start_activity(activity)
            msg = f"Started {activity}"
    except (ValueError, KeyError) as exc:
        msg = f"Error: {exc}"
    return redirect(url_for("index", msg=msg))

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


from flask import send_file, make_response

@app.route("/export", methods=["POST"])
def export():
    """Export both detailed and summary CSVs, display summary, and provide detailed CSV download."""
    try:
        month_value = request.form.get("month", "")
        year_str, month_str = month_value.split("-")
        year, month = int(year_str), int(month_str)
        # Export detailed CSV to disk
        detailed_path = Path("reports") / f"report-{year:04d}-{month:02d}.csv"
        tracker.export_monthly_csv(year, month, detailed_path)
        # Generate summary table in memory
        entries = tracker.monthly_entries(year, month)
        summary = {}
        for entry in entries:
            activity = entry["activity"]
            summary.setdefault(activity, 0)
            summary[activity] += entry["duration_seconds"]
        summary_table = [
        {
            "activity": activity,
            "total_seconds": total_seconds,
            "total_hours": f"{total_seconds / 3600:.2f}",
        }
        for activity, total_seconds in summary.items()
        ]
        # Provide download link for detailed CSV
        detailed_csv_url = url_for("download_csv", year=year, month=month)
        return render_template_string(
        HTML_TEMPLATE,
        **get_context(f"Exported {len(entries)} entries for {year}-{month:02d}"),
        summary_table=summary_table,
        detailed_csv_url=detailed_csv_url,
        )
    except (ValueError, KeyError) as exc:
        return redirect(url_for("index", msg=f"Error: {exc}"))

@app.route("/download_csv/<int:year>-<int:month>.csv")
def download_csv(year, month):
    """Serve the detailed monthly CSV as a file download."""
    detailed_path = Path("reports") / f"report-{year:04d}-{month:02d}.csv"
    if not detailed_path.exists():
        return make_response("File not found", 404)
    return send_file(detailed_path, as_attachment=True, download_name=detailed_path.name)

if __name__ == "__main__":
    app.run(debug=True)
