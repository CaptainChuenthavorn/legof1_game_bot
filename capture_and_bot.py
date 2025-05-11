import cv2
import numpy as np
import mss
import win32gui
import time
import pyautogui
import keyboard

# === Screen and Mouse Helper ===
def get_client_area(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd == 0:
        raise Exception(f"Window '{window_name}' not found!")
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])
    return {'left': left, 'top': top, 'width': right - left, 'height': bottom - top}

def move_mouse_linear(x, y, duration=0.3):
    pyautogui.moveTo(x, y, duration=duration)

def click_mouse():
    pyautogui.click()

def move_and_click_relative_linear(monitor, offset_x, offset_y, description=""):
    target_x = monitor['left'] + offset_x
    target_y = monitor['top'] + offset_y
    move_mouse_linear(target_x, target_y)
    print(f"[✓] Moved mouse to {description}" if description else "[✓] Moved mouse")
    click_mouse()

# === Timer Detection ===
def detect_timer_start(frame):
    # Simple check: white text at top right in timer format "0:00.000s"
    roi = frame[10:40, frame.shape[1]-160:frame.shape[1]-10]  # top-right
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    white_ratio = np.sum(thresh == 255) / thresh.size
    return white_ratio > 0.7  # heuristic

# === Main Flow ===
def run_bot_sequence(window_name):
    monitor = get_client_area(window_name)
    print("[*] Window found:", monitor)

    # Step 1: Move mouse to top-left to refresh
    move_mouse_linear(monitor['left'] + 95, monitor['top'] + 63)
    pyautogui.press('f5')
    print("[✓] Page refreshed")
    time.sleep(3)

    # Step 2: Click "Play Game"
    move_and_click_relative_linear(monitor, 462, 567, "Play Game")
    time.sleep(1)

    # Step 3: Type year
    pyautogui.write("2001")
    time.sleep(1)

    # Step 4: Click Start Race
    move_and_click_relative_linear(monitor, 467, 427, "Start Race")

    # Step 5: Wait for timer to hit 0:00.000 and then hold right arrow
    print("[*] Waiting for timer...")
    with mss.mss() as sct:
        while True:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            if detect_timer_start(frame):
                print("[✓] Timer started — go!")
                keyboard.press('right')
                break

    # Optionally: release the key after N seconds
    time.sleep(5)
    keyboard.release('right')
    print("[✓] Stopped right arrow key after 5 seconds.")

# === Run it ===
if __name__ == "__main__":
    run_bot_sequence("LEGO® - Google Chrome")
