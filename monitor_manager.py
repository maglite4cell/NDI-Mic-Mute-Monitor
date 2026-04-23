import socket
import threading
import time
import httpx
from state import state
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_message_builder import OscMessageBuilder

class GlobalMonitor:
    def __init__(self, monitor_type):
        self.monitor_type = monitor_type
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        pass

    def stop(self):
        self.running = False

    def get_interested_leds(self):
        """Returns a list of led_configs that are currently enabled and use this monitor type."""
        return [l for l in state.get_leds() if l.get("enabled", True) and l.get("monitor_type", "") == self.monitor_type]

class GlobalShureManager(GlobalMonitor):
    def __init__(self):
        self.connected = False
        self.sock = None
        self.buffer = ""
        self.last_sync_time = 0
        self.current_ip = None
        self.current_port = None
        super().__init__("shure")

    def run(self):
        print(f"Global Shure Manager: Started")
        while self.running:
            conn_config = state.config.get("connections", {}).get("shure", {})
            ip = conn_config.get("ip", "127.0.0.1")
            port = int(conn_config.get("port", 2202))

            if ip != self.current_ip or port != self.current_port:
                self.disconnect()
                self.current_ip = ip
                self.current_port = port

            if not self.connected:
                self.connect()
            
            if self.connected:
                if time.time() - self.last_sync_time > 30.0:
                    self.last_sync_time = time.time()
                    for ch in range(1, 5):
                        self.send_command(f"< GET {ch} CHAN_NAME >")
                        self.send_command(f"< GET {ch} RF_ANTENNA >")
                        self.send_command(f"< GET {ch} BATT_CHARGE >")
                
                try:
                    data = self.sock.recv(1024)
                    if not data:
                        print(f"Global Shure: Remote closed connection")
                        self.disconnect()
                        continue
                    self.process_data(data.decode('utf-8', errors='ignore'))
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Global Shure: Error {e}")
                        self.disconnect()
            else:
                time.sleep(1.0)
    
    def connect(self):
        if not self.current_ip: return
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0)
            self.sock.connect((self.current_ip, self.current_port))
            self.connected = True
            print(f"Global Shure: Connected to {self.current_ip}:{self.current_port}!")
            
            for ch in range(1, 5):
                self.send_command(f"< GET {ch} CHAN_NAME >")
                self.send_command(f"< GET {ch} TX_TYPE >")
                self.send_command(f"< GET {ch} TX_MUTE_STATUS >")
                self.send_command(f"< GET {ch} RF_ANTENNA >")
                self.send_command(f"< GET {ch} BATT_CHARGE >")
        except Exception as e:
            print(f"Global Shure: Connection to {self.current_ip}:{self.current_port} failed: {e}")

    def send_command(self, cmd):
        if self.sock and self.connected:
            try:
                self.sock.sendall(cmd.encode('utf-8'))
            except Exception:
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
        if len(self.buffer) > 8192:
            self.buffer = ""
            return
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
        parts = msg.split()
        if len(parts) < 4 or parts[0] != "REP":
            return
        
        target_ch = parts[1]
        command = parts[2]
        value = " ".join(parts[3:])

        leds = self.get_interested_leds()
        
        for led in leds:
            if led.get("target") != target_ch:
                continue
                
            lid = led["id"]
            if command in ["CHANNEL_NAME", "CHAN_NAME"]:
                if led.get("use_receiver_name", True):
                    name = value.strip('"{}').strip()
                    state.update_single_led(lid, name=name)
            
            elif command == "BATT_CHARGE":
                try:
                    if value == "255" or value == "UNKN":
                        state.update_single_led(lid, battery=None)
                    else:
                        batt = int(value)
                        state.update_single_led(lid, battery=batt)
                except ValueError:
                    pass

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
                    state.update_single_led(lid, status=status_val)


class GlobalOscManager(GlobalMonitor):
    def __init__(self, monitor_type):
        self.server = None
        self.server_thread = None
        self.current_ip = None
        self.current_port = None
        super().__init__(monitor_type)
        
    def osc_handler(self, address, *args):
        if not args: return
        val = args[0]
        
        leds = self.get_interested_leds()
        for led in leds:
            if led.get("target") == address:
                # X32: 0 is Mute, 1 is Unmute. 
                # WING: 1 is Mute, 0 is Unmute.
                if self.monitor_type == "x32":
                    status = "OK" if val == 1 else "MUTE"
                elif self.monitor_type == "wing":
                    status = "MUTE" if val == 1 else "OK"
                else:
                    status = "OK" if val == 1 else "MUTE"
                    
                state.update_single_led(led["id"], status=status)

    def run(self):
        print(f"Global {self.monitor_type.upper()} Manager: Started")
        
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self.osc_handler)

        while self.running:
            conn_config = state.config.get("connections", {}).get(self.monitor_type, {})
            ip = conn_config.get("ip", "127.0.0.1")
            port = int(conn_config.get("port", 10023 if self.monitor_type == "x32" else 2223))

            if ip != self.current_ip or port != self.current_port:
                self.current_ip = ip
                self.current_port = port
                
                if self.server:
                    self.server.shutdown()
                    self.server.server_close()
                    if self.server_thread:
                        self.server_thread.join()
                    
                try:
                    # Bind to port 0 to let OS pick an available local port
                    self.server = BlockingOSCUDPServer(("0.0.0.0", 0), dispatcher)
                    self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                    self.server_thread.start()
                    print(f"Global {self.monitor_type.upper()} Manager: Bound OSC listener to {self.server.server_address}")
                except Exception as e:
                    print(f"Error starting {self.monitor_type} server: {e}")

            if self.server and self.current_ip and self.current_port and self.current_ip != "127.0.0.1":
                # Send keep-alive using the server's socket so replies route back to our listener
                try:
                    builder = OscMessageBuilder(address="/xremote")
                    msg = builder.build()
                    self.server.socket.sendto(msg.dgram, (self.current_ip, self.current_port))
                except Exception as e:
                    pass
                    
            time.sleep(8.0) # /xremote expires in 10s


class GlobalMonitorManager:
    def __init__(self):
        self.managers = [
            GlobalShureManager(),
            GlobalOscManager("x32"),
            GlobalOscManager("wing")
        ]

    def run(self):
        print("Monitor Manager Started.")
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass

def run_monitor_clients():
    manager = GlobalMonitorManager()
    manager.run()
