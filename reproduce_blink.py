
import time

def test_blink(interval_ms, duration_sec):
    print(f"Testing blinking with interval {interval_ms}ms for {duration_sec} seconds")
    start_time = time.time()
    last_state = None
    
    changes = 0
    
    while time.time() - start_time < duration_sec:
        current_time_ms = int(time.time() * 1000)
        is_on = (current_time_ms // interval_ms) % 2 == 0
        
        state_str = "ON" if is_on else "OFF"
        if state_str != last_state:
            print(f"{current_time_ms}: {state_str}")
            last_state = state_str
            changes += 1
        
        time.sleep(0.01) # 100Hz check

    print(f"Total changes: {changes}")

test_blink(500, 3)
test_blink(100, 1)
test_blink(2000, 5)
