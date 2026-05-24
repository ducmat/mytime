"""
Unit tests for the TimeTracker class.
Tests activity addition, tracking, persistence, and CSV export functionality.
"""

import csv
from datetime import datetime

from tracker import TimeTracker


def test_add_start_stop_and_persist(tmp_path):
    """
    Test adding an activity, starting and stopping it, and persisting the data.
    """
    db = tmp_path / "test_mytime.yml"
    tracker = TimeTracker(db)

    tracker.add_activity("Coding")
    assert tracker.list_activities() == ["Coding"]

    tracker.start_activity("Coding", now=datetime(2026, 5, 1, 9, 0, 0))
    entry = tracker.stop_activity(now=datetime(2026, 5, 1, 10, 30, 0))

    assert entry["activity"] == "Coding"
    assert entry["duration_seconds"] == 5400
    assert tracker.load_data()["running"] is None


def test_export_monthly_csv(tmp_path):
    """
    Test exporting a monthly CSV report and verify its contents.
    """
    db = tmp_path / "test_mytime.yml"
    tracker = TimeTracker(db)

    tracker.start_activity("Planning", now=datetime(2026, 5, 1, 8, 0, 0))
    tracker.stop_activity(now=datetime(2026, 5, 1, 9, 0, 0))
    tracker.start_activity("Planning", now=datetime(2026, 4, 1, 8, 0, 0))
    tracker.stop_activity(now=datetime(2026, 4, 1, 9, 0, 0))

    report = tmp_path / "report.csv"
    count = tracker.export_monthly_csv(2026, 5, report)

    assert count == 1

    with report.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["activity"] == "Planning"
    assert rows[0]["duration_seconds"] == "3600"
    assert rows[0]["duration_hours"] == "1.00"
