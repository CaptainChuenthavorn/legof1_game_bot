from playwright.sync_api import sync_playwright
import time
import pyautogui
import win32gui
import keyboard
import cv2
import numpy as np
import mss
import threading

# === Window & screen tools ===
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

def countdown_message(task_description, seconds=3):
    for i in range(seconds, 0, -1):
        print(f"🕒 {task_description} in {i} second{'s' if i > 1 else ''}...")
        time.sleep(1)

# === AI Driving Logic ===
def ai_drive_loop(window_name: str, duration=15):
    monitor = get_client_area(window_name)
    with mss.mss() as sct:
        start_time = time.time()
        print("[*] AI driving...")

        while time.time() - start_time < duration:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            # === Color filtering to detect white/yellow lines ===
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Define range for white line
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 50, 255])
            # mask_white = cv2.inRange(hsv, lower_white, upper_white)
            mask_white = cv2.inRange(hsv, lower_white, upper_white)

            # You can try this if your line is yellowish instead
            # lower_yellow = np.array([20, 100, 100])
            # upper_yellow = np.array([30, 255, 255])
            # mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

            height, width = mask_white.shape
            center_x = width // 2
            sample_rows = [height - 100, height - 80, height - 60]

            line_positions = []

            for y in sample_rows:
                row = mask_white[y]
                non_zero_x = np.where(row > 0)[0]
                if len(non_zero_x) > 0:
                    avg_x = int(np.mean(non_zero_x))
                    line_positions.append(avg_x)
                    cv2.circle(frame, (avg_x, y), 5, (0, 255, 0), -1)
                else:
                    line_positions.append(center_x)  # fallback

            # Average line center
            if line_positions:
                avg_line_x = int(np.mean(line_positions))
                offset = avg_line_x - center_x

                if offset < -10:
                    keyboard.press('left')
                    keyboard.release('right')
                elif offset > 10:
                    keyboard.press('right')
                    keyboard.release('left')
                else:
                    keyboard.release('left')
                    keyboard.release('right')

                # Debug line
                cv2.line(frame, (avg_line_x, sample_rows[0]), (avg_line_x, sample_rows[-1]), (0, 255, 255), 2)
                cv2.line(frame, (center_x, sample_rows[0]), (center_x, sample_rows[-1]), (255, 0, 0), 2)

            cv2.imshow("AI View - Improved Detection", mask_white)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Cleanup
        keyboard.release('left')
        keyboard.release('right')
        cv2.destroyAllWindows()
        print("[✓] AI driving complete.")


# === Main Orchestration ===
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

        print("[*] Waiting for timer to hit 0:00.000...")
        page.wait_for_selector(".game__ui__stats__text--time", timeout=30000)

        while True:
            timer_text = page.inner_text(".game__ui__stats__text--time").strip()
            print("Current timer:", timer_text)
            if timer_text.startswith("0:00"):
                print("[✓] Timer started! AI Driving begins...")
                break
            time.sleep(0.05)

        # Start AI driving thread
        t1 = threading.Thread(target=ai_drive_loop, args=("LEGO® - Chromium",), daemon=True)
        t1.start()
        t1.join()

# === Entry Point ===
if __name__ == "__main__":
    run_game_bot("https://f1-contest.com/versions/th/lazada/en.html?utm_source=meta_traf&utm_medium=image&_campaign=lazada_f1_game&utm_campaign=lazada_f1_game&utm_id=7052025&utm_content=boost")
