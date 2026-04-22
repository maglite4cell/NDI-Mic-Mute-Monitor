import pytest
from fastapi.testclient import TestClient
from web_server import app

client = TestClient(app)

def test_get_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "NDI Monitor Config" in response.text

def test_get_config_api():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "leds" in data
    assert "show_preview" in data

def test_post_config_api():
    # Fetch current
    res = client.get("/api/config")
    current_data = res.json()
    
    # Toggle 'show_preview'
    new_preview = not current_data.get("show_preview", True)
    
    payload = {
        "leds": [{"id": 0, "name": "API_UPDATED_MIC"}],
        "show_preview": new_preview
    }
    
    response = client.post("/api/config", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["config"]["show_preview"] == new_preview
    assert data["config"]["leds"][0]["name"] == "API_UPDATED_MIC"
