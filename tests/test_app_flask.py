"""
Integration tests for the Flask version of the MyTime Tracker app.
"""
import pytest
from tracker import TimeTracker
from app_flask import app as flask_app

@pytest.fixture
def client(tmp_path):
    """Set up the Flask test client with a temporary database for testing."""
    # Patch the tracker to use a temp db
    flask_app.config["TESTING"] = True
    db_path = tmp_path / "mytime.yml"
    flask_app.tracker = TimeTracker(db_path)
    with flask_app.test_client() as client_test:
        yield client_test

def test_index_page(client): # pylint: disable=redefined-outer-name
    """Test that the index page loads successfully and contains expected content."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"MyTime Tracker" in resp.data

def test_add_activity(client): # pylint: disable=redefined-outer-name
    """Test adding a new activity and verifying it appears on the index page."""
    resp = client.post("/add", data={"name": "TestActivity"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Activity added" in resp.data
    assert b"TestActivity" in resp.data

def test_start_and_stop_activity(client): # pylint: disable=redefined-outer-name
    """Test starting and stopping an activity and verifying the status messages."""
    client.post("/add", data={"name": "TestActivity"}, follow_redirects=True)
    resp = client.post("/start", data={"activity": "TestActivity"}, follow_redirects=True)
    assert b"Tracking started" in resp.data
    resp = client.post("/stop", follow_redirects=True)
    assert b"Stopped TestActivity" in resp.data

def test_export_monthly_csv(client): # pylint: disable=redefined-outer-name
    """Test exporting a monthly CSV report and verifying the status message."""
    client.post("/add", data={"name": "TestActivity"}, follow_redirects=True)
    client.post("/start", data={"activity": "TestActivity"}, follow_redirects=True)
    client.post("/stop", follow_redirects=True)
    resp = client.post("/export", data={"month": "2026-05"}, follow_redirects=True)
    assert b"Exported" in resp.data
