import time
import keyboard

def record_left_right_macro(wait_for_timer_start_fn):
    print("[⌛] Waiting for game timer to start...")

    # Wait for your game's timer to reach "0:00"
    while True:
        timer_text = wait_for_timer_start_fn()
        if timer_text.startswith("0:00"):
            print("[✓] Timer started! Recording keys...")
            break
        time.sleep(0.1)

    start_time = time.time()
    macro_events = []

    print("[📝] Press ← or → arrows to record. Press ESC to stop.")

    while True:
        event = keyboard.read_event()
        now = time.time()
        elapsed = round(now - start_time, 3)

        # Only record left/right arrow keys on key down
        if event.event_type == "down" and event.name in ["left", "right"]:
            print(f"{elapsed}s — {event.name}")
            macro_events.append((elapsed, event.name))

        if event.name == "esc":
            print("[🛑] Stopped recording.")
            break
