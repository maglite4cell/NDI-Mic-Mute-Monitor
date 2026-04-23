import pytest
import time
from unittest.mock import patch, MagicMock
from monitor_manager import GlobalShureManager, GlobalOscManager, GlobalMonitorManager
from state import state

@pytest.fixture(autouse=True)
def reset_state():
    """Reset the global state before each test."""
    state.config["connections"] = {
        "shure": {"ip": "127.0.0.1", "port": 2202},
        "x32": {"ip": "192.168.1.100", "port": 10023},
        "wing": {"ip": "192.168.1.101", "port": 2223}
    }
    state.config["leds"] = [
        {"id": 0, "enabled": True, "monitor_type": "shure", "target": "1"},
        {"id": 1, "enabled": True, "monitor_type": "x32", "target": "/ch/01/mix/on"},
        {"id": 2, "enabled": True, "monitor_type": "wing", "target": "/ch/02/mute"}
    ]
    state.save_config()
    yield

def test_shure_parsing():
    manager = GlobalShureManager()
    
    # Simulate receiving a valid name message for target "1"
    manager.parse_message("REP 1 CHAN_NAME {Test Mic}")
    leds = state.get_leds()
    assert leds[0]["name"] == "Test Mic"
    
    # Simulate receiving a battery message
    manager.parse_message("REP 1 BATT_CHARGE 85")
    leds = state.get_leds()
    assert leds[0]["battery"] == 85
    
    # Simulate TX status
    manager.parse_message("REP 1 AUDIO_TX_ON_OFF ON")
    leds = state.get_leds()
    assert leds[0]["status"] == "OK"
    
    manager.parse_message("REP 1 AUDIO_TX_ON_OFF OFF")
    leds = state.get_leds()
    assert leds[0]["status"] == "MUTE"
    
    manager.stop()

def test_osc_x32_parsing():
    manager = GlobalOscManager("x32")
    
    # Mute OFF (1) -> OK in X32
    manager.osc_handler("/ch/01/mix/on", 1)
    leds = state.get_leds()
    assert leds[1]["status"] == "OK"
    
    # Mute ON (0) -> MUTE in X32
    manager.osc_handler("/ch/01/mix/on", 0)
    leds = state.get_leds()
    assert leds[1]["status"] == "MUTE"
    
    manager.stop()

def test_osc_wing_parsing():
    manager = GlobalOscManager("wing")
    
    # Mute ON (1) -> MUTE in WING
    manager.osc_handler("/ch/02/mute", 1)
    leds = state.get_leds()
    assert leds[2]["status"] == "MUTE"
    
    # Mute OFF (0) -> OK in WING
    manager.osc_handler("/ch/02/mute", 0)
    leds = state.get_leds()
    assert leds[2]["status"] == "OK"
    
    manager.stop()
