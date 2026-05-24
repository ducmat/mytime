from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class TimeTracker:
    def __init__(self, db_path: str | Path = "mytime.yml") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            self.save_data({"activities": [], "entries": [], "running": None})

    def load_data(self) -> dict[str, Any]:
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
        self.db_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    def list_activities(self) -> list[str]:
        return sorted(self.load_data()["activities"])

    def add_activity(self, name: str) -> None:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Activity name cannot be empty")

        data = self.load_data()
        if cleaned not in data["activities"]:
            data["activities"].append(cleaned)
            self.save_data(data)

    def start_activity(self, name: str, now: datetime | None = None) -> None:
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
        entries = self.load_data()["entries"]
        result = []
        for entry in entries:
            start = datetime.fromisoformat(entry["start"])
            if start.year == year and start.month == month:
                result.append(entry)
        return result

    def export_monthly_csv(self, year: int, month: int, output_path: str | Path) -> int:
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
