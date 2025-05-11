#not working method mouse position cause chromium resolution is default 1200x800, old chrome i capture is 800,800 
import cv2
import numpy as np
import mss
import win32gui
import time
import pyautogui
import keyboard
from playwright.sync_api import sync_playwright

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

# === Full Bot Flow with Playwright Timer ===
def run_bot_with_playwright(window_name, url):
    # Step 1: Start Playwright and open game
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        # browser = p.chromium.launch_persistent_context(
        #     user_data_dir="C:/Users/ADMINN/AppData/Local/Google/Chrome/User Data",
        #     headless=False,
        #     channel="chrome"
        # )

        page = browser.new_page()
        page.goto(url)

        print("[*] Opened browser and loading game...")
        time.sleep(6)

        # Step 2: Now do all the bot UI interactions
        monitor = get_client_area(window_name)
        print("[*] Window found:", monitor)

        #refresh page
        # move_mouse_linear(monitor['left'] + 95, monitor['top'] + 63)
        # pyautogui.press('f5')
        # print("[✓] Page refreshed")
        # time.sleep(3)

        move_and_click_relative_linear(monitor, 462, 567, "Play Game")
        time.sleep(1)

        pyautogui.write("2001")
        time.sleep(1)

        move_and_click_relative_linear(monitor, 467, 427, "Start Race")

        # Step 3: Wait for the DOM timer to start
        print("[*] Waiting for DOM timer to hit 0:00.000...")
        page.wait_for_selector(".game__ui__stats__text--time", timeout=40000)

        while True:
            timer_text = page.inner_text(".game__ui__stats__text--time").strip()
            print("Current timer:", timer_text)
            if timer_text.startswith("0:00"):
                print("[✓] Timer started! Launching bot...")
                break
            time.sleep(0.1)

        # Step 4: Trigger the key press
        keyboard.press('right')
        time.sleep(5)
        keyboard.release('right')
        print("[✓] Bot movement complete.")
        input("[*] Press Enter to exit...")

# === Run Bot ===
if __name__ == "__main__":
    run_bot_with_playwright(
        "LEGO® - Chromium",
        "https://f1-contest.com/versions/th/lazada/en.html?utm_source=meta_traf&utm_medium=image&_campaign=lazada_f1_game&utm_campaign=lazada_f1_game&utm_id=7052025&utm_content=boost&fbclid=IwY2xjawKNDrpleHRuA2FlbQIxMABicmlkETFmeFcwN1VvQ2VlUmJQV3RVAR5PVfdjYvdCNQJaSQkSsxHEijzq_q9rzdRqQ_hXyUph2GkLYf2MNNBo4fJl-Q_aem_4Jnql_TSVyyYYKB7pMEN7w"
    )
