import json
import threading
import os
import sys
import platform

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
else:
    # Running from source — config lives next to this file, not the CWD
    CONFIG_FILE = os.path.join(_script_dir, "config.json")

DEFAULT_CONFIG = {
    "show_preview": True,
    "show_leds": True,
    "show_names": True,
    "layout_mode": "fixed",
    "leds": [
        {"id": i, 
         "name": f"MIC {i+1}", 
         "enabled": True, 
         "interval": 500,
         "shure_ip": "127.0.0.1", 
         "shure_port": 2202,
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
                # Merge top-level scalar keys
                for k, v in saved.items():
                    if k != "leds":
                        merged[k] = v
                # Merge LED list by id
                saved_leds = {led["id"]: led for led in saved.get("leds", [])}
                for led in merged["leds"]:
                    if led["id"] in saved_leds:
                        led.update(saved_leds[led["id"]])
            except json.JSONDecodeError:
                print("Error decoding config.json, using defaults.")

        self.config = merged
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
