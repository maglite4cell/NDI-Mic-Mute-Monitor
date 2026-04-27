import json
import threading
import os
import sys
import platform
import logging
from logging.handlers import RotatingFileHandler

# Determine config file location
_script_dir = os.path.dirname(os.path.abspath(__file__))

if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle — store config in user's app data dir
    _system = platform.system()
    if _system == 'Darwin':
        config_dir = os.path.expanduser("~/Library/Application Support/NDI Shure Monitor")
    elif _system == 'Windows':
        config_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NDI Shure Monitor")
    else:  # Linux / other
        config_dir = os.path.expanduser("~/.config/NDI Shure Monitor")
    os.makedirs(config_dir, exist_ok=True)
    CONFIG_FILE = os.path.join(config_dir, "config.json")
    LOG_FILE = os.path.join(config_dir, "debug.log")
else:
    # Running from source — config lives next to this file, not the CWD
    CONFIG_FILE = os.path.join(_script_dir, "config.json")
    LOG_FILE = os.path.join(_script_dir, "debug.log")

logger = logging.getLogger("ndi_shure_monitor")
handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=1)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

DEFAULT_CONFIG = {
    "enable_debug_logging": False,
    "show_preview": True,
    "show_leds": True,
    "show_names": True,
    "show_battery": True,
    "layout_mode": "fixed",
    "connections": {
        "shure": {"ip": "127.0.0.1", "port": 2202},
        "x32": {"ip": "192.168.1.100", "port": 10023},
        "wing": {"ip": "192.168.1.101", "port": 2223},
        "sennheiser": {"ip": "127.0.0.1", "port": 53212},
        "presonus": {"ip": "127.0.0.1", "port": 0}
    },
    "leds": [
        {"id": i, 
         "name": f"MIC {i+1}", 
         "enabled": True, 
         "interval": 500,
         "monitor_type": "shure",
         "target": f"{i+1}",
         "ip": "127.0.0.1",
         "port": 2202,
         "use_receiver_name": True,
         "use_live_status": True
        }
        for i in range(6)
    ]
}

class StateManager:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StateManager, cls).__new__(cls)
                    cls._instance.load_config()
        return cls._instance

    def load_config(self):
        """Load config from disk, merging on top of DEFAULT_CONFIG so new keys are never missing."""
        merged = {k: v for k, v in DEFAULT_CONFIG.items()}  # shallow top-level copy
        # Deep-copy the led list so defaults aren't mutated
        merged["leds"] = [dict(led) for led in DEFAULT_CONFIG["leds"]]

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    saved = json.load(f)
                
                old_leds = saved.get("leds", [])
                
                # Merge top-level scalar keys and connections dict
                for k, v in saved.items():
                    if k == "connections":
                        for c_type, c_data in v.items():
                            if c_type in merged["connections"]:
                                merged["connections"][c_type].update(c_data)
                    elif k != "leds":
                        merged[k] = v
                        
                # Merge LED list by id
                saved_leds = {led["id"]: led for led in old_leds}
                for led in merged["leds"]:
                    if led["id"] in saved_leds:
                        saved_led = saved_leds[led["id"]]
                        
                        # Migration: If it's a shure/sennheiser mic and lacks individual IP, 
                        # use the global one from the saved config (if present) or the default.
                        m_type = saved_led.get("monitor_type", led["monitor_type"])
                        if m_type in ["shure", "sennheiser"]:
                            if "ip" not in saved_led:
                                # Try to find the global IP for this type in the saved config
                                global_conn = saved.get("connections", {}).get(m_type, {})
                                saved_led["ip"] = global_conn.get("ip", merged["connections"][m_type]["ip"])
                            if "port" not in saved_led:
                                global_conn = saved.get("connections", {}).get(m_type, {})
                                saved_led["port"] = global_conn.get("port", merged["connections"][m_type]["port"])

                        if m_type == "shure" and "target" not in saved_led:
                             # Default shure target is its index+1
                             saved_led["target"] = str(led["id"] + 1)
                             
                        # Strip out old fields
                        saved_led.pop("shure_ip", None)
                        saved_led.pop("shure_port", None)
                        saved_led.pop("api_endpoint", None)
                        
                        led.update(saved_led)
            except json.JSONDecodeError:
                print("Error decoding config.json, using defaults.")

        self.config = merged
        
        if self.config.get("enable_debug_logging", False):
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            
        self.save_config()

    def save_config(self):
        with self._lock:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)

    def get_leds(self):
        with self._lock:
            return self.config.get("leds", [])

    def update_led(self, led_id, updates):
        with self._lock:
            for led in self.config["leds"]:
                if led["id"] == led_id:
                    led.update(updates)
                    break
            self.save_config()



    def update_single_led(self, index, **kwargs):
        with self._lock:
             # Sanity check
            if 0 <= index < len(self.config["leds"]):
                led = self.config["leds"][index]
                for k, v in kwargs.items():
                    led[k] = v
                self.save_config()

# Global accessor
state = StateManager()
