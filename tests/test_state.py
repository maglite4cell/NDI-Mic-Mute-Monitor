import os
import json
import pytest
import tempfile
from state import StateManager, DEFAULT_CONFIG

@pytest.fixture
def mock_state():
    # Store old config file path if it exists
    old_file = None
    import state
    old_file = state.CONFIG_FILE
    
    # Use a temporary file for config.json during tests
    temp_fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(temp_fd)
    
    state.CONFIG_FILE = temp_path
    
    # Force fresh instance for test
    StateManager._instance = None
    sm = StateManager()
    
    yield sm
    
    # Cleanup
    os.remove(temp_path)
    state.CONFIG_FILE = old_file
    StateManager._instance = None

def test_load_default_config(mock_state):
    # State should load default if file is empty/invalid/missing
    assert mock_state.config["show_preview"] == DEFAULT_CONFIG["show_preview"]
    assert len(mock_state.config["leds"]) == len(DEFAULT_CONFIG["leds"])

def test_save_and_reload_config(mock_state):
    # Change a config value
    mock_state.config["show_preview"] = not DEFAULT_CONFIG["show_preview"]
    mock_state.save_config()
    
    # Re-instantiate
    import state
    StateManager._instance = None
    sm2 = StateManager()
    
    assert sm2.config["show_preview"] != DEFAULT_CONFIG["show_preview"]

def test_update_single_led(mock_state):
    # Test LED update
    mock_state.update_single_led(0, name="TEST_MIC", status="OK")
    leds = mock_state.get_leds()
    assert leds[0]["name"] == "TEST_MIC"
    assert leds[0]["status"] == "OK"
