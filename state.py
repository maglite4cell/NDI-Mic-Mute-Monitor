import json
import threading
import os
import sys

# Determine config file location
# When bundled, use Application Support directory; otherwise use current directory
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    config_dir = os.path.expanduser("~/Library/Application Support/NDI Shure Monitor")
    os.makedirs(config_dir, exist_ok=True)
    CONFIG_FILE = os.path.join(config_dir, "config.json")
else:
    # Running in normal Python environment
    CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "show_preview": True,
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
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
            except json.JSONDecodeError:
                print("Error decoding config.json, using default.")
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.config = DEFAULT_CONFIG.copy()
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
