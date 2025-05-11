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
def ai_drive_loop(window_name: str, duration=120):
    monitor = get_client_area(window_name)
    with mss.mss() as sct:
        start_time = time.time()
        print("[*] AI driving...")

        while time.time() - start_time < duration:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 50, 255])
            mask_white = cv2.inRange(hsv, lower_white, upper_white)

            height, width = mask_white.shape
            center_x = width // 2

            # === ROI near the car ===
            roi_width = 50
            roi_height = 100

            roi_x = center_x - roi_width // 2
            roi_y = height // 2  # shift vertically near the bottom

            # Ensure it stays in bounds
            roi_x = max(0, min(roi_x, width - roi_width))
            roi_y = max(0, min(roi_y, height - roi_height))

            roi = mask_white[roi_y : roi_y + roi_height, roi_x : roi_x + roi_width]


            # === Contour detection to ignore small white junk ===
            contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            valid_centers = []

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 100:
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        valid_centers.append(cx)

            print(f"Contours: {len(valid_centers)}")

            if valid_centers:
                avg_line_x = int(np.mean(valid_centers))
                roi_center_x = roi.shape[1] // 2
                offset = avg_line_x - roi_center_x
                print(f"Offset from center: {offset}")


                if offset < -10:
                    keyboard.press('left')
                    keyboard.release('right')
                elif offset > 10:
                    keyboard.press('right')
                    keyboard.release('left')
                else:
                    keyboard.release('left')
                    keyboard.release('right')

                # Debug visual
                debug_view = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)
                for cx in valid_centers:
                    cv2.circle(debug_view, (cx, roi.shape[0] // 2), 5, (0, 255, 0), -1)
                cv2.line(debug_view, (roi_center_x, 0), (roi_center_x, roi.shape[0]), (255, 0, 0), 1)
                cv2.imshow("ROI", debug_view)

            else:
                keyboard.release('left')
                keyboard.release('right')
                # cv2.imshow("AI ROI", roi)
                # On full frame
                cv2.rectangle(frame,
                            (roi_x, roi_y),
                            (roi_x + roi_width, roi_y + roi_height),
                            (0, 255, 255), 2)
                cv2.imshow("Full Frame with ROI", frame)


            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

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
