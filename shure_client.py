import socket
import threading
import time
from state import state

class ShureConnection:
    def __init__(self, led_id, ip, port):
        self.led_id = led_id
        self.ip = ip
        self.port = int(port)
        self.running = True
        self.connected = False
        self.sock = None
        self.buffer = ""
        self.last_sync_time = 0
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        print(f"Shure Ch {self.led_id+1}: Starting connection to {self.ip}:{self.port}")
        while self.running:
            if not self.connected:
                self.connect()
            
            if self.connected:
                # Periodic sync for names and RF status (every 30 seconds)
                if time.time() - self.last_sync_time > 30.0:
                    self.last_sync_time = time.time()
                    for ch in range(1, 5):
                        self.send_command(f"< GET {ch} CHAN_NAME >")
                        self.send_command(f"< GET {ch} RF_ANTENNA >")
                
                try:
                    data = self.sock.recv(1024)
                    if not data:
                        print(f"Shure Ch {self.led_id+1}: Remote closed connection")
                        self.disconnect()
                        continue
                    self.process_data(data.decode('utf-8', errors='ignore'))
                except socket.timeout:
                    continue
                except Exception as e:
                    # SystemError: [Errno 35] Resource temporarily unavailable (non-blocking)
                    # or other socket errors
                    if self.running:
                        print(f"Shure Ch {self.led_id+1}: Error {e}")
                        self.disconnect()
            else:
                time.sleep(1.0)
    
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0)
            self.sock.connect((self.ip, self.port))
            self.connected = True
            print(f"Shure Ch {self.led_id+1}: Connected!")
            
            # Request initial state
            for ch in range(1, 5):
                # Standard Shure commands
                self.send_command(f"< GET {ch} CHAN_NAME >")
                self.send_command(f"< GET {ch} TX_TYPE >")
                self.send_command(f"< GET {ch} TX_MUTE_STATUS >")
                self.send_command(f"< GET {ch} RF_ANTENNA >")
        except Exception:
            # Silent retry
            pass

    def send_command(self, cmd):
        if self.sock and self.connected:
            try:
                self.sock.sendall(cmd.encode('utf-8'))
            except Exception as e:
                pass

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.sock = None
        self.connected = False

    def process_data(self, raw_data):
        self.buffer += raw_data
        while '>' in self.buffer:
            if '<' in self.buffer:
                start = self.buffer.find('<')
                end = self.buffer.find('>')
                if start != -1 and end != -1 and start < end:
                    msg = self.buffer[start+1:end]
                    self.parse_message(msg)
                    self.buffer = self.buffer[end+1:]
                else:
                    break
            else:
                self.buffer = ""

    def parse_message(self, msg):
        # Format: REP x COMMAND VALUE
        print(f"DEBUG RECV (Ch {self.led_id+1}): {msg}")
        
        parts = msg.split()
        if len(parts) < 4 or parts[0] != "REP":
            return
        
        # NOTE: Receiver might report "REP 1 ...", but since this connection
        # is dedicated to THIS specific LED ID, we ignore the channel index from the packet
        # and always apply it to self.led_id.
        
        command = parts[2]
        value = " ".join(parts[3:])

        # Get current config to check toggles
        leds = state.get_leds()
        if self.led_id >= len(leds): return
        led_config = leds[self.led_id]

        if command in ["CHANNEL_NAME", "CHAN_NAME"]:
            if led_config.get("use_receiver_name", True):
                name = value.strip('"{}').strip()
                print(f"Shure Ch {self.led_id+1}: Name -> {name}")
                state.update_single_led(self.led_id, name=name)
        
        elif command in ["AUDIO_TX_ON_OFF", "TX_MUTE_STATUS", "TX_TYPE", "BATT_BARS", "RF_ANTENNA"]:
            status_val = None
            if command == "AUDIO_TX_ON_OFF":
                status_val = "OK" if value == "ON" else "MUTE"
            elif command == "TX_MUTE_STATUS":
                if value != "UNKN":
                    status_val = "OK" if value == "OFF" else "MUTE"
            elif command == "TX_TYPE":
                status_val = "MUTE" if value == "UNKN" else "OK"
            elif command == "BATT_BARS":
                status_val = "MUTE" if value == "255" else "OK"
            elif command == "RF_ANTENNA":
                status_val = "MUTE" if value == "XX" else "OK"
                
            if status_val is not None:
                print(f"Shure Ch {self.led_id+1}: TX [{command}] -> {status_val}")
                state.update_single_led(self.led_id, status=status_val)

    def stop(self):
        self.running = False
        self.disconnect()


class ShureManager:
    def __init__(self):
        self.connections = {} # led_id -> ShureConnection
        
    def run(self):
        print("Shure Manager Started: Monitoring configs...")
        while True:
            leds = state.get_leds()
            active_ids = []

            for led in leds:
                lid = led["id"]
                enabled = led.get("enabled", True)
                ip = led.get("shure_ip", "127.0.0.1")
                port = led.get("shure_port", 2202)
                
                if not enabled:
                    # If helper exists, kill it
                    self.stop_connection(lid)
                    continue

                active_ids.append(lid)
                
                # Check if exists
                if lid in self.connections:
                    conn = self.connections[lid]
                    # Check if config changed
                    if conn.ip != ip or conn.port != int(port):
                        print(f"Shure Ch {lid+1}: Config changed. Restarting connection.")
                        self.stop_connection(lid)
                        self.start_connection(lid, ip, port)
                else:
                    # Start new
                    self.start_connection(lid, ip, port)
            
            time.sleep(2.0)

    def start_connection(self, led_id, ip, port):
        self.connections[led_id] = ShureConnection(led_id, ip, port)

    def stop_connection(self, led_id):
        if led_id in self.connections:
            self.connections[led_id].stop()
            del self.connections[led_id]

def run_shure_client():
    manager = ShureManager()
    manager.run()
