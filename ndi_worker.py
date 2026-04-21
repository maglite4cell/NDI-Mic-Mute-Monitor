import time
import pygame
import numpy as np
import threading
import os
import sys
from state import state

class SuppressStdout:
    def __enter__(self):
        try:
            self._original_stdout = os.dup(1)
            # self._original_stderr = os.dup(2) # Keep stderr
            self._devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(self._devnull, 1)
            # os.dup2(self._devnull, 2)
        except Exception:
            self._original_stdout = None
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._original_stdout:
            try:
                os.dup2(self._original_stdout, 1)
                # os.dup2(self._original_stderr, 2)
                os.close(self._original_stdout)
                # os.close(self._original_stderr)
                os.close(self._devnull)
            except Exception:
                pass

try:
    import NDIlib as ndi
    NDI_AVAILABLE = True
except ImportError:
    print("NDIlib not found. Running in Mock Mode.")
    NDI_AVAILABLE = False
except Exception as e:
    print(f"NDIlib error: {e}. Running in Mock Mode.")
    NDI_AVAILABLE = False

class NDIWorker:
    def __init__(self, width=1920, height=1080, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.running = True

    def run(self):
        ndi_send = None
        if NDI_AVAILABLE:
            # Initialize NDI
            if not ndi.initialize():
                print("Could not initialize NDI.")
            else:
                send_settings = ndi.SendCreate()
                send_settings.ndi_name = "ShureMonitor"
                ndi_send = ndi.send_create(send_settings)
                
                if ndi_send is None:
                    print("Could not create NDI sender.")
                else:
                    video_frame = ndi.VideoFrameV2()
                    video_frame.xres = self.width
                    video_frame.yres = self.height
                    video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_RGBA
                    video_frame.frame_rate_N = 30000
                    video_frame.frame_rate_D = 1001
                    video_frame.line_stride_in_bytes = self.width * 4

        # Initialize PyGame
        pygame.init()
        pygame.display.set_caption("NDI Shure Monitor (Preview)")

        # Create a surface for drawing (Transparent)
        screen = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Create a visible window for preview (conditionally shown)
        display_window = pygame.display.set_mode((self.width, self.height), pygame.HIDDEN)
        preview_visible = False
        
        font = pygame.font.SysFont("Arial", 40, bold=True)
        
        # Timing
        clock = pygame.time.Clock()

        print("NDI Worker Started.")
        frame_count = 0

        while self.running:
            # Handle Window Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # Clear screen (Transparent)
            screen.fill((0, 0, 0, 0))

            # Get State
            leds = state.get_leds()

            # Draw Layout
            # Top 1/8th = 135 pixels
            section_height = self.height // 8
            width_per_led = self.width // 6
            
            current_time_ms = int(time.time() * 1000)

            for i, led in enumerate(leds):
                if not led.get("enabled", True):
                    continue

                x_center = i * width_per_led + (width_per_led // 2)
                y_center = 50
                radius = 30

                # Status / Logic
                use_live = led.get("use_live_status", True)
                status = led.get("status", "MUTE") # Default to MUTE/Red if no signal
                interval = led.get("interval", 500)
                
                color = (100, 100, 100, 255) # Gray default

                if use_live:
                    # LIVE MODE: Green if OK/ON, Red if MUTE/OFF
                    if status == "OK" or status == "ON":
                        color = (0, 255, 0, 255) # Green
                    else:
                        color = (255, 0, 0, 255) # Red
                else:
                    # MANUAL BLINK MODE
                    if interval <= 0: interval = 500
                    is_on = (current_time_ms // interval) % 2 == 0
                    color = (0, 255, 0, 255) if is_on else (255, 0, 0, 255)
                
                # Draw LED (Circle)
                pygame.draw.circle(screen, color, (x_center, y_center), radius)
                
                # Draw Text
                name = led.get("name", f"Mic {i+1}")
                text_surf = font.render(name, True, (255, 255, 255, 255))
                text_rect = text_surf.get_rect(center=(x_center, y_center + 50))
                screen.blit(text_surf, text_rect)


            # Convert to NDI buffer
            if NDI_AVAILABLE and ndi_send:
                try:
                    data_bytes = pygame.image.tobytes(screen, 'RGBA')
                    # Must convert to numpy and reshape for NDI wrapper to read dims correctly
                    frame_data = np.frombuffer(data_bytes, dtype=np.uint8)
                    frame_data = frame_data.reshape((self.height, self.width, 4))
                    video_frame.data = frame_data
                    
                    # Suppress library noise and use Sync send 
                    with SuppressStdout():
                         ndi.send_send_video_v2(ndi_send, video_frame)
                        
                except Exception as e:
                    sys.stderr.write(f"NDI Send Error: {e}\n")
                    pass
            
            # --- Local Preview ---
            # Check if we should show preview
            show_preview = state.config.get("show_preview", True)
            
            if show_preview and not preview_visible:
                # Show the window
                pygame.display.set_mode((self.width, self.height))
                preview_visible = True
            elif not show_preview and preview_visible:
                # Hide the window
                pygame.display.set_mode((self.width, self.height), pygame.HIDDEN)
                preview_visible = False
            
            if show_preview:
                # Fill background with dark gray to visualize transparency
                display_window.fill((30, 30, 30)) 
                # Blit the transparent layer on top
                display_window.blit(screen, (0, 0))
                # Update display
                pygame.display.flip()

            clock.tick(self.fps)

        # Cleanup
        if NDI_AVAILABLE and ndi_send:
            ndi.send_destroy(ndi_send)
            ndi.destroy()
        pygame.quit()
