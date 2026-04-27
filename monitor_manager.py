import socket
import threading
import time
import json
from state import state
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.osc_message_builder import OscMessageBuilder

class BaseConnection:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.running = True
        self.connected = False
        self.last_sync_time = 0
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        pass

    def stop(self):
        self.running = False
        self.disconnect()

    def disconnect(self):
        self.connected = False

    def get_leds_for_this_connection(self, monitor_type):
        return [l for l in state.get_leds() 
                if l.get("enabled", True) 
                and l.get("monitor_type") == monitor_type 
                and l.get("ip") == self.ip 
                and int(l.get("port", 0)) == self.port]

class ShureConnection(BaseConnection):
    def __init__(self, ip, port):
        self.sock = None
        self.buffer = ""
        super().__init__(ip, port)

    def run(self):
        while self.running:
            if not self.connected:
                self.connect()
            
            if self.connected:
                # Periodic sync every 30s
                if time.time() - self.last_sync_time > 30.0:
                    self.last_sync_time = time.time()
                    self.sync_all()
                
                try:
                    data = self.sock.recv(1024)
                    if not data:
                        self.disconnect()
                        continue
                    self.process_data(data.decode('utf-8', errors='ignore'))
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Shure Connection ({self.ip}): Error {e}")
                        self.disconnect()
            else:
                time.sleep(2.0)

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0)
            self.sock.connect((self.ip, self.port))
            self.connected = True
            print(f"Shure: Connected to {self.ip}:{self.port}")
            self.sync_all()
        except Exception as e:
            pass

    def disconnect(self):
        super().disconnect()
        if self.sock:
            try: self.sock.close()
            except: pass
        self.sock = None

    def sync_all(self):
        # Shure receivers usually have 1-4 channels
        for ch in range(1, 5):
            self.send_command(f"< GET {ch} CHAN_NAME >")
            self.send_command(f"< GET {ch} TX_MUTE_STATUS >")
            self.send_command(f"< GET {ch} BATT_CHARGE >")
            self.send_command(f"< GET {ch} RF_ANTENNA >")

    def send_command(self, cmd):
        if self.sock and self.connected:
            try:
                self.sock.sendall(cmd.encode('utf-8'))
            except:
                pass

    def process_data(self, raw_data):
        self.buffer += raw_data
        if len(self.buffer) > 8192: self.buffer = ""
        while '>' in self.buffer:
            if '<' in self.buffer:
                start = self.buffer.find('<')
                end = self.buffer.find('>')
                if start < end:
                    msg = self.buffer[start+1:end]
                    self.parse_message(msg)
                    self.buffer = self.buffer[end+1:]
                else:
                    self.buffer = self.buffer[end+1:]
            else:
                self.buffer = ""

    def parse_message(self, msg):
        parts = msg.split()
        if len(parts) < 4 or parts[0] != "REP": return
        
        target_ch = parts[1]
        command = parts[2]
        value = " ".join(parts[3:])

        leds = self.get_leds_for_this_connection("shure")
        for led in leds:
            if led.get("target") != target_ch: continue
            
            lid = led["id"]
            if command in ["CHANNEL_NAME", "CHAN_NAME"]:
                if led.get("use_receiver_name", True):
                    name = value.strip('"{}').strip()
                    state.update_single_led(lid, name=name)
            elif command == "BATT_CHARGE":
                try:
                    val = int(value)
                    state.update_single_led(lid, battery=None if val == 255 else val)
                except: pass
            elif command in ["AUDIO_TX_ON_OFF", "TX_MUTE_STATUS", "RF_ANTENNA"]:
                status = "OK"
                if command == "TX_MUTE_STATUS" and value == "ON": status = "MUTE"
                elif command == "AUDIO_TX_ON_OFF" and value == "OFF": status = "MUTE"
                elif command == "RF_ANTENNA" and value == "XX": status = "MUTE"
                state.update_single_led(lid, status=status)

class SennheiserConnection(BaseConnection):
    def __init__(self, ip, port):
        self.sock = None
        super().__init__(ip, port)

    def run(self):
        while self.running:
            if not self.connected:
                self.connect()
            
            if self.connected:
                if time.time() - self.last_sync_time > 30.0:
                    self.last_sync_time = time.time()
                    self.sync_all()
                
                try:
                    data = self.sock.recv(2048)
                    if not data:
                        self.disconnect()
                        continue
                    self.process_data(data.decode('utf-8', errors='ignore'))
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Sennheiser Connection ({self.ip}): Error {e}")
                        self.disconnect()
            else:
                time.sleep(2.0)

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0)
            self.sock.connect((self.ip, self.port))
            self.connected = True
            print(f"Sennheiser: Connected to {self.ip}:{self.port}")
            self.sync_all()
        except:
            pass

    def disconnect(self):
        super().disconnect()
        if self.sock:
            try: self.sock.close()
            except: pass
        self.sock = None

    def sync_all(self):
        # SSC Get for all mics (EW-D/DX usually 1 or 2 channels)
        # Using a broad query for all mic properties
        self.send_msg({"ssc": "1.0", "method": "get", "params": {"mics": None}})

    def send_msg(self, obj):
        if self.sock and self.connected:
            try:
                msg = json.dumps(obj) + "\r\n"
                self.sock.sendall(msg.encode('utf-8'))
            except: pass

    def process_data(self, raw_data):
        # Sennheiser SSC is newline delimited JSON
        for line in raw_data.splitlines():
            try:
                data = json.loads(line)
                self.parse_ssc(data)
            except: continue

    def parse_ssc(self, data):
        # Simple recursive parser for SSC params
        if "params" not in data: return
        mics = data["params"].get("mics", {})
        if not mics: return
        
        leds = self.get_leds_for_this_connection("sennheiser")
        for ch_str, ch_data in mics.items():
            for led in leds:
                if led.get("target") != ch_str: continue
                
                updates = {}
                if "mute" in ch_data:
                    updates["status"] = "MUTE" if ch_data["mute"] else "OK"
                if "name" in ch_data and led.get("use_receiver_name", True):
                    updates["name"] = ch_data["name"]
                if "battery" in ch_data and "percentage" in ch_data["battery"]:
                    updates["battery"] = ch_data["battery"]["percentage"]
                
                if updates:
                    state.update_single_led(led["id"], **updates)

class GlobalOscManager:
    def __init__(self, monitor_type):
        self.monitor_type = monitor_type
        self.server = None
        self.server_thread = None
        self.current_ip = None
        self.current_port = None
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self.osc_handler)
        
        while self.running:
            conn_config = state.config.get("connections", {}).get(self.monitor_type, {})
            ip = conn_config.get("ip", "127.0.0.1")
            port = int(conn_config.get("port", 10023 if self.monitor_type == "x32" else 2223))

            if ip != self.current_ip or port != self.current_port:
                self.current_ip = ip
                self.current_port = port
                self.restart_server(dispatcher)

            if self.server and self.current_ip != "127.0.0.1":
                try:
                    builder = OscMessageBuilder(address="/xremote")
                    msg = builder.build()
                    self.server.socket.sendto(msg.dgram, (self.current_ip, self.current_port))
                except: pass
            
            time.sleep(8.0)

    def restart_server(self, dispatcher):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        try:
            self.server = BlockingOSCUDPServer(("0.0.0.0", 0), dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            print(f"OSC {self.monitor_type}: Listener bound to {self.server.server_address}")
        except Exception as e:
            print(f"OSC {self.monitor_type}: Server error {e}")

    def osc_handler(self, address, *args):
        if not args: return
        val = args[0]
        leds = [l for l in state.get_leds() if l.get("enabled", True) and l.get("monitor_type") == self.monitor_type]
        for led in leds:
            if led.get("target") == address:
                status = "OK"
                if self.monitor_type == "x32": status = "OK" if val == 1 else "MUTE"
                elif self.monitor_type == "wing": status = "MUTE" if val == 1 else "OK"
                state.update_single_led(led["id"], status=status)

class GlobalMonitorManager:
    def __init__(self):
        self.connections = {} # key: (type, ip, port) -> connection object
        self.mixers = [GlobalOscManager("x32"), GlobalOscManager("wing")]
        self.running = True

    def run(self):
        print("Monitor Manager (v2) Started.")
        while self.running:
            self.update_connections()
            time.sleep(5.0)

    def update_connections(self):
        active_configs = set()
        leds = state.get_leds()
        
        for led in leds:
            if not led.get("enabled", True): continue
            m_type = led.get("monitor_type")
            if m_type not in ["shure", "sennheiser"]: continue
            
            ip = led.get("ip", "127.0.0.1")
            port = int(led.get("port", 0))
            if ip == "127.0.0.1" or port == 0: continue
            
            config_key = (m_type, ip, port)
            active_configs.add(config_key)
            
            if config_key not in self.connections:
                print(f"Manager: Spawning new {m_type} connection to {ip}:{port}")
                if m_type == "shure":
                    self.connections[config_key] = ShureConnection(ip, port)
                elif m_type == "sennheiser":
                    self.connections[config_key] = SennheiserConnection(ip, port)

        # Cleanup old connections
        for key in list(self.connections.keys()):
            if key not in active_configs:
                print(f"Manager: Closing stale connection {key}")
                self.connections[key].stop()
                del self.connections[key]

def run_monitor_clients():
    manager = GlobalMonitorManager()
    manager.run()
