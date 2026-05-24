"""
Integration tests for the Flask version of the MyTime Tracker app.
"""
import pytest
from tracker import TimeTracker
from app_flask import app as flask_app

@pytest.fixture
def client_test(tmp_path):
    """Set up the Flask test client with a temporary database for testing."""
    # Patch the tracker to use a temp db
    flask_app.config["TESTING"] = True
    db_path = tmp_path / "mytime.yml"
    flask_app.tracker = TimeTracker(db_path)
    with flask_app.test_client() as client_test:
        yield client_test

def test_index_page(client_test):
    """Test that the index page loads successfully and contains expected content."""
    resp = client_test.get("/")
    assert resp.status_code == 200
    assert b"MyTime Tracker" in resp.data

def test_add_activity(client_test):
    """Test adding a new activity and verifying it appears on the index page."""
    resp = client_test.post("/add", data={"name": "TestActivity"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Activity added" in resp.data
    assert b"TestActivity" in resp.data

def test_start_and_stop_activity(client_test):
    """Test starting and stopping an activity and verifying the status messages."""
    client_test.post("/add", data={"name": "TestActivity"}, follow_redirects=True)
    resp = client_test.post("/start", data={"activity": "TestActivity"}, follow_redirects=True)
    assert b"Tracking started" in resp.data
    resp = client_test.post("/stop", follow_redirects=True)
    assert b"Stopped TestActivity" in resp.data

def test_export_monthly_csv(client_test):
    """Test exporting a monthly CSV report and verifying the status message."""
    client_test.post("/add", data={"name": "TestActivity"}, follow_redirects=True)
    client_test.post("/start", data={"activity": "TestActivity"}, follow_redirects=True)
    client_test.post("/stop", follow_redirects=True)
    resp = client_test.post("/export", data={"month": "2026-05"}, follow_redirects=True)
    assert b"Exported" in resp.data
