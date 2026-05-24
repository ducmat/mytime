
"""
TimeTracker Class for Activity Logging
-------------------------------------
This module defines the TimeTracker class, which manages activities, time entries, 
and running sessions.
It supports adding activities, starting/stopping tracking, 
and exporting monthly reports to CSV.

Data is stored in a YAML file (default: mytime.yml) with the following structure:
    - activities: list of activity names
    - entries: list of tracked time entries
    - running: currently running activity (if any)

Methods:
    - load_data, save_data
    - list_activities, add_activity
    - start_activity, stop_activity
    - monthly_entries, export_monthly_csv
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class TimeTracker:
    """
    Manages activity tracking, time entries, and running sessions.
    Stores data in a YAML file and provides methods to add activities,
    start/stop tracking, and export monthly reports.
    """

    def __init__(self, db_path: str | Path = "mytime.yml") -> None:
        """
        Initialize the TimeTracker.
        Creates the database file if it does not exist.

        Args:
            db_path (str | Path): Path to the YAML database file.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            self.save_data({"activities": [], "entries": [], "running": None})

    def load_data(self) -> dict[str, Any]:
        """
        Load and return the current data from the YAML file.

        Returns:
            dict[str, Any]: Dictionary with keys 'activities', 'entries', and 'running'.
        """
        if not self.db_path.exists():
            return {"activities": [], "entries": [], "running": None}

        raw = yaml.safe_load(self.db_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {"activities": [], "entries": [], "running": None}

        return {
            "activities": list(raw.get("activities") or []),
            "entries": list(raw.get("entries") or []),
            "running": raw.get("running"),
        }

    def save_data(self, data: dict[str, Any]) -> None:
        """
        Save the provided data dictionary to the YAML file.

        Args:
            data (dict[str, Any]): Data to save.
        """
        self.db_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    def list_activities(self) -> list[str]:
        """
        Return a sorted list of all activity names.

        Returns:
            list[str]: Sorted activity names.
        """
        return sorted(self.load_data()["activities"])

    def add_activity(self, name: str) -> None:
        """
        Add a new activity name if it does not already exist.

        Args:
            name (str): Name of the activity to add.

        Raises:
            ValueError: If the activity name is empty.
        """
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Activity name cannot be empty")

        data = self.load_data()
        if cleaned not in data["activities"]:
            data["activities"].append(cleaned)
            self.save_data(data)

    def start_activity(self, name: str, now: datetime | None = None) -> None:
        """
        Start tracking a new activity.
        Records the start time and sets the activity as running.

        Args:
            name (str): Name of the activity to start.
            now (datetime, optional): Custom start time. Defaults to current time.

        Raises:
            ValueError: If another activity is already running or name is empty.
        """
        data = self.load_data()
        if data["running"] is not None:
            raise ValueError("Another activity is already running")

        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Activity name cannot be empty")

        if cleaned not in data["activities"]:
            data["activities"].append(cleaned)

        start_time = (now or datetime.now()).isoformat(timespec="seconds")
        data["running"] = {"activity": cleaned, "start": start_time}
        self.save_data(data)

    def stop_activity(self, now: datetime | None = None) -> dict[str, Any]:
        """
        Stop the currently running activity and record its entry.

        Args:
            now (datetime, optional): Custom stop time. Defaults to current time.

        Returns:
            dict[str, Any]: The entry for the stopped activity.

        Raises:
            ValueError: If no activity is running.
        """
        data = self.load_data()
        running = data["running"]
        if running is None:
            raise ValueError("No running activity to stop")

        end_time = now or datetime.now()
        start_time = datetime.fromisoformat(running["start"])
        duration_seconds = max(int((end_time - start_time).total_seconds()), 0)

        entry = {
            "activity": running["activity"],
            "start": start_time.isoformat(timespec="seconds"),
            "end": end_time.isoformat(timespec="seconds"),
            "duration_seconds": duration_seconds,
        }

        data["entries"].append(entry)
        data["running"] = None
        self.save_data(data)
        return entry

    def monthly_entries(self, year: int, month: int) -> list[dict[str, Any]]:
        """
        Get all entries for a specific month and year.

        Args:
            year (int): The year to filter entries.
            month (int): The month to filter entries.

        Returns:
            list[dict[str, Any]]: List of entries for the given month.
        """
        entries = self.load_data()["entries"]
        result = []
        for entry in entries:
            start = datetime.fromisoformat(entry["start"])
            if start.year == year and start.month == month:
                result.append(entry)
        return result

    def export_monthly_csv(self, year: int, month: int, output_path: str | Path) -> int:
        """
        Export all entries for a given month to a CSV file.

        Args:
            year (int): The year to export.
            month (int): The month to export.
            output_path (str | Path): Path to the output CSV file.

        Returns:
            int: Number of entries exported.
        """
        entries = self.monthly_entries(year, month)
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=["activity", "start", "end", "duration_seconds", "duration_hours"],
            )
            writer.writeheader()
            for entry in entries:
                writer.writerow(
                    {
                        "activity": entry["activity"],
                        "start": entry["start"],
                        "end": entry["end"],
                        "duration_seconds": entry["duration_seconds"],
                        "duration_hours": f"{entry['duration_seconds'] / 3600:.2f}",
                    }
                )

        return len(entries)
