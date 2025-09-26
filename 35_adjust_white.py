import cv2
import numpy as np
import mss
import time
from playwright.sync_api import sync_playwright
import cv2
import numpy as np
import mss
import win32gui
import time
import pyautogui
import keyboard

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
def get_client_area(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd == 0:
        raise Exception(f"Window '{window_name}' not found!")
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])
    return {'left': left, 'top': top, 'width': right - left, 'height': bottom - top}

def get_line_direction_and_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Detect white line, then invert to follow black line
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 50, 255])
    mask = cv2.inRange(hsv, lower_white, upper_white)
    # mask = cv2.bitwise_not(mask)

    direction = "lost"
    cx = None  # Default if line not found

    M = cv2.moments(mask)
    if M["m00"] > 0:
        cx = int(M["m10"] / M["m00"])
        center_offset = cx - (frame.shape[1] // 2)

        if center_offset < -10:
            direction = "left"
        elif center_offset > 10:
            direction = "right"
        else:
            direction = "center"

    return direction, mask, cx

def track_and_control():
    # Your tracking region (adjust if needed)
    x1, y1 =607, 350
    x2, y2 =670, 420
    monitor = get_client_area("LEGO® - Google Chrome")
    with mss.mss() as sct:
        while True:
            img = sct.grab(monitor)
            full_frame = np.array(img)
            full_frame = cv2.cvtColor(full_frame, cv2.COLOR_BGRA2BGR)

            # Crop just the region you want to track
            # frame = full_frame[y1:y2, x1:x2]
            # direction, mask, cx = get_line_direction_and_mask(frame)

            # full_frame = np.array(sct.grab(sct.monitors[1]))
            # full_frame = cv2.cvtColor(full_frame, cv2.COLOR_BGRA2BGR)

            frame = full_frame[y1:y2, x1:x2]
            direction, mask, cx = get_line_direction_and_mask(frame)

            # Show debug window
            vis = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            if cx is not None:
                cv2.circle(vis, (cx, frame.shape[0] // 2), 4, (0, 255, 0), -1)
                cv2.line(vis, (frame.shape[1] // 2, 0), (frame.shape[1] // 2, frame.shape[0]), (0, 0, 255), 1)
            cv2.imshow("White Line Tracker", vis)

            # Control logic
            if direction == "left":
                keyboard.press("left")
                keyboard.release("right")
            elif direction == "right":
                keyboard.press("right")
                keyboard.release("left")
            elif direction == "center":
                keyboard.release("left")
                keyboard.release("right")
            else:  # lost
                keyboard.release("left")
                keyboard.release("right")

            print("Direction:", direction)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    keyboard.release("left")
    keyboard.release("right")
    cv2.destroyAllWindows()


def run():
    with sync_playwright() as p:

        
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context()
        page = context.new_page()

        print("[*] Setting up game...")
        page.goto("https://f1-contest.com/versions/th/lazada/en.html")

        page.wait_for_selector("button.cta-button.cta-button--normal")
        page.click("button.cta-button.cta-button--normal")
        time.sleep(1)
        page.keyboard.type("2001")
        time.sleep(1)
        monitor = get_client_area("LEGO® - Google Chrome")
        move_and_click_relative_linear(monitor, 865, 700, "Start Race")
        # time.sleep(1)
        # Step 4: Click Start Race
        page.wait_for_selector("button.cta-button.cta-button--normal")
        page.click("button.cta-button.cta-button--normal")

        print("[*] Waiting for game timer to start...")
        page.wait_for_selector(".game__ui__stats__text--time", timeout=30000)
        while True:
            timer_text = page.inner_text(".game__ui__stats__text--time").strip()
            if timer_text.startswith("0:00"):
                print("[✅] Timer Start!")
                break
            time.sleep(0.05)
        # macro = record_left_right_macro()
        # Insert after your timer check in your run() function

        # play_macro(macro_events)


        # Start line tracking once the race begins
        track_and_control()

if __name__ == "__main__":
    run()
