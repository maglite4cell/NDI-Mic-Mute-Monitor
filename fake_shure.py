import socket
import time
import random
import threading

HOST = '127.0.0.1'
PORT = 2202

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        # Simulate some initial state
        for i in range(1, 7):
            msg = f"<REP {i} CHANNEL_NAME \"Sim Mic {i}\">"
            conn.sendall(msg.encode())
            time.sleep(0.1)

        while True:
            # Pick a random channel
            ch = random.randint(1, 6)
            
            # Randomly toggle ON/OFF
            status = "ON" if random.random() > 0.5 else "OFF"
            msg = f"<REP {ch} AUDIO_TX_ON_OFF {status}>"
            
            print(f"Sending: {msg}")
            conn.sendall(msg.encode())
            
            # Occasionally change name
            if random.random() > 0.9:
                new_name = f"Singer {random.randint(1, 99)}"
                msg = f"<REP {ch} CHANNEL_NAME \"{new_name}\">"
                print(f"Sending: {msg}")
                conn.sendall(msg.encode())
                
            time.sleep(2.0)
    except BrokenPipeError:
        print(f"Client {addr} disconnected.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def main():
    print(f"Fake Shure Receiver listening on {HOST}:{PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.start()

if __name__ == "__main__":
    main()
