"""
Integration tests for the BaseHTTPRequestHandler version of the MyTime Tracker app.
"""
import subprocess
import time
import requests
import os
import pytest

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

@pytest.fixture(scope="module")
def server(tmp_path_factory):
    """Start the MyTime Tracker HTTP server in a subprocess and yield control to the tests."""
    tmp_dir = tmp_path_factory.mktemp("mytime_http")
    env = os.environ.copy()
    env["MYTIME_DB"] = str(tmp_dir / "mytime.yml")
    proc = subprocess.Popen([
        "python", "app.py"
    ], cwd=os.path.dirname(__file__) + "/..", env=env)
    # Wait for server to start
    time.sleep(1.5)
    yield
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_index_page():
    """Test that the index page loads successfully and contains expected content."""
    resp = requests.get(SERVER_URL + "/")
    assert resp.status_code == 200
    assert "MyTime Tracker" in resp.text

def test_add_activity():
    """Test adding a new activity and verifying it appears on the index page."""
    resp = requests.post(SERVER_URL + "/add", data={"name": "TestActivity"}, allow_redirects=True)
    assert resp.status_code in (200, 303)
    # Follow redirect if needed
    if resp.status_code == 303:
        resp = requests.get(SERVER_URL + "/")
    assert "TestActivity" in resp.text

def test_start_and_stop_activity():
    """Test starting and stopping an activity and verifying the status messages."""
    requests.post(SERVER_URL + "/add", data={"name": "TestActivity"})
    resp = requests.post(SERVER_URL + "/start",
                         data={"activity": "TestActivity"},
                         allow_redirects=True)
    assert resp.status_code in (200, 303)
    resp = requests.post(SERVER_URL + "/stop", allow_redirects=True)
    assert resp.status_code in (200, 303)
    # Check stopped message
    resp = requests.get(SERVER_URL + "/")
    assert "Stopped TestActivity" in resp.text or "No activity running" in resp.text

def test_export_monthly_csv():
    """Test exporting a monthly CSV report and verifying the status message."""
    requests.post(SERVER_URL + "/add", data={"name": "TestActivity"})
    requests.post(SERVER_URL + "/start", data={"activity": "TestActivity"})
    requests.post(SERVER_URL + "/stop")
    resp = requests.post(SERVER_URL + "/export", data={"month": "2026-05"}, allow_redirects=True)
    assert resp.status_code in (200, 303)
    resp = requests.get(SERVER_URL + "/")
    assert "Exported" in resp.text
