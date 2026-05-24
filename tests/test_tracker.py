import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tracker import TimeTracker


class TimeTrackerTests(unittest.TestCase):
    def test_add_start_stop_and_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "mytime.yml"
            tracker = TimeTracker(db)

            tracker.add_activity("Coding")
            self.assertEqual(tracker.list_activities(), ["Coding"])

            tracker.start_activity("Coding", now=datetime(2026, 5, 1, 9, 0, 0))
            entry = tracker.stop_activity(now=datetime(2026, 5, 1, 10, 30, 0))

            self.assertEqual(entry["activity"], "Coding")
            self.assertEqual(entry["duration_seconds"], 5400)
            self.assertIsNone(tracker.load_data()["running"])

    def test_export_monthly_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "mytime.yml"
            tracker = TimeTracker(db)

            tracker.start_activity("Planning", now=datetime(2026, 5, 1, 8, 0, 0))
            tracker.stop_activity(now=datetime(2026, 5, 1, 9, 0, 0))
            tracker.start_activity("Planning", now=datetime(2026, 4, 1, 8, 0, 0))
            tracker.stop_activity(now=datetime(2026, 4, 1, 9, 0, 0))

            report = Path(tmp) / "report.csv"
            count = tracker.export_monthly_csv(2026, 5, report)

            self.assertEqual(count, 1)

            with report.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["activity"], "Planning")
            self.assertEqual(rows[0]["duration_seconds"], "3600")
            self.assertEqual(rows[0]["duration_hours"], "1.00")


if __name__ == "__main__":
    unittest.main()
