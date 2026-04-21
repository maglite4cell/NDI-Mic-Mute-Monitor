import threading
import time
from ndi_worker import NDIWorker
from web_server import run_server

def main():
    print("Starting NDI Shure Monitor...")
    
    # Start Web Server in a Daemon Thread
    print("Starting Web Interface on http://0.0.0.0:8001")
    web_thread = threading.Thread(target=run_server, daemon=True)
    web_thread.start()

    # Start Shure Client in a Daemon Thread
    from shure_client import run_shure_client
    print("Starting Shure Client...")
    shure_thread = threading.Thread(target=run_shure_client, daemon=True)
    shure_thread.start()

    # Start NDI Worker on Main Thread (Required for PyGame/SDL on macOS)
    ndi_worker = NDIWorker()
    try:
        ndi_worker.run() # This blocks
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        ndi_worker.running = False
        print("Done.")

if __name__ == "__main__":
    main()
