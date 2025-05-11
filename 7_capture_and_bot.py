# implement capture to start after select redbull car ,start race
from playwright.sync_api import sync_playwright
import time
import pyautogui
import win32gui
import keyboard
import cv2
import numpy as np
import mss
import threading

def countdown_message(task_description, seconds=3):
    for i in range(seconds, 0, -1):
        print(f"🕒 {task_description} in {i} second{'s' if i > 1 else ''}...")
        time.sleep(1)

def get_client_area(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd == 0:
        raise Exception(f"Window '{window_name}' not found!")
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])
    return {'left': left, 'top': top, 'width': right - left, 'height': bottom - top}

def click_red_bull_card(window_title):
    monitor = get_client_area(window_title)
    print(f"Window bounds: {monitor}")
    x = monitor['left'] + 865
    y = monitor['top'] + 700
    pyautogui.moveTo(x, y, duration=0.4)
    pyautogui.click()
    print(f"[✓] Hovered and clicked Red Bull at ({x}, {y})")

def capture_window_realtime(window_name, duration=5):
    monitor = get_client_area(window_name)
    with mss.mss() as sct:
        print("[*] Capturing client area. Press 'q' to quit early.")
        start_time = time.time()
        while time.time() - start_time < duration:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            cv2.imshow("Window Capture", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

# === Thread 1: Hold right arrow
def press_right_key(duration=5):
    keyboard.press('right')
    print("[*] Holding RIGHT key...")
    time.sleep(duration)
    keyboard.release('right')
    print("[✓] Released RIGHT key.")

# === Thread 2: Capture screen
def threaded_screen_capture():
    capture_window_realtime("LEGO® - Chromium", duration=180)

def run_game_bot(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--window-size=1280,800"])
        page = browser.new_page()
        page.goto(url)
        
        print("[*] Waiting for Play Game button...")
        page.wait_for_selector("button.cta-button.cta-button--normal")
        page.click("button.cta-button.cta-button--normal")
        print("[✓] Clicked Play Game")

        countdown_message('Wait for enter year', 1)
        print("[*] Entering birth year...")
        page.keyboard.type("2001")
        print("[✓] Year submitted")

        time.sleep(1)
        click_red_bull_card("LEGO® - Chromium")

        print("[*] Clicking Start Race...")
        page.wait_for_selector("button.cta-button.cta-button--normal")
        page.click("button.cta-button.cta-button--normal")
        print("[✓] Race started")
        # t2 = threading.Thread(target=threaded_screen_capture)
        # t2.start()
        # print("[*] Waiting for timer to hit 0:00.000...")
        # page.wait_for_selector(".game__ui__stats__text--time", timeout=30000)

        # while True:
        #     timer_text = page.inner_text(".game__ui__stats__text--time").strip()
        #     print("Current timer:", timer_text)
        #     if timer_text.startswith("0:00"):
        #         print("[✓] Timer started! Driving...")
        #         break
        #     time.sleep(0.05)
        
        # # === Start both threads
        # t1 = threading.Thread(target=press_right_key)
        

        # t1.start()
        

        # t1.join()
        # t2.join()
        # === Start screen capture before timer
        t2 = threading.Thread(target=threaded_screen_capture, daemon=True)
        t2.start()

        # Wait for 0:00 timer
        print("[*] Waiting for timer to hit 0:00.000...")
        page.wait_for_selector(".game__ui__stats__text--time", timeout=30000)

        while True:
            timer_text = page.inner_text(".game__ui__stats__text--time").strip()
            print("Current timer:", timer_text)
            if timer_text.startswith("0:00"):
                print("[✓] Timer started! Driving...")
                break
            time.sleep(0.05)

        # Start right-arrow drive
        t1 = threading.Thread(target=press_right_key, daemon=True)
        t1.start()

        # Wait for both to finish
        t1.join()
        t2.join()

if __name__ == "__main__":
    run_game_bot("https://f1-contest.com/versions/th/lazada/en.html?utm_source=meta_traf&utm_medium=image&_campaign=lazada_f1_game&utm_campaign=lazada_f1_game&utm_id=7052025&utm_content=boost")