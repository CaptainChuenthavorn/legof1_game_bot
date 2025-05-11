#implement bot for chromium to start game
from playwright.sync_api import sync_playwright
import time
import pyautogui
import win32gui
import keyboard
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

    # Approximate position of Red Bull from your screenshots (adjust if needed)
    x = monitor['left'] + 865
    y = monitor['top'] + 700

    pyautogui.moveTo(x, y, duration=0.4)
    pyautogui.click()
    print(f"[✓] Hovered and clicked Red Bull at ({x}, {y})")

    # print(f"[✓] Clicked Red Bull at ({x}, {y})")

def run_game_bot(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--window-size=1280,800"])
        page = browser.new_page()
        page.goto(url)
        
        # countdown_message('wait for P')
        print("[*] Waiting for Play Game button...")
        page.wait_for_selector("button.cta-button.cta-button--normal")
        page.click("button.cta-button.cta-button--normal")
        print("[✓] Clicked Play Game")
        
        countdown_message('Wait for enter year',1)
        print("[*] Entering birth year...")
        page.keyboard.type("2001")
       

        print("[✓] Year submitted")

        time.sleep(1)
        click_red_bull_card("LEGO® - Chromium")



        # Click START RACE button
        print("[*] Clicking Start Race...")
        page.wait_for_selector("button.cta-button.cta-button--normal")
        page.click("button.cta-button.cta-button--normal")
        print("[✓] Race started")

        # Wait for the timer
        print("[*] Waiting for timer to hit 0:00.000...")
        page.wait_for_selector(".game__ui__stats__text--time", timeout=30000)

        while True:
            timer_text = page.inner_text(".game__ui__stats__text--time").strip()
            print("Current timer:", timer_text)
            if timer_text.startswith("0:00"):
                print("[✓] Timer started! Driving...")
                break
            time.sleep(0.05)

        # Press right arrow to drive
        keyboard.press('right')
        time.sleep(5)
        keyboard.release('right')
        print("[✓] Released right arrow")

# === Run the Bot ===
if __name__ == "__main__":
    run_game_bot("https://f1-contest.com/versions/th/lazada/en.html?utm_source=meta_traf&utm_medium=image&_campaign=lazada_f1_game&utm_campaign=lazada_f1_game&utm_id=7052025&utm_content=boost")
