import asyncio
import time
import numpy as np
import cv2
import mss
import pyautogui
import keyboard
import win32gui
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import DQN
from stable_baselines3.common.env_checker import check_env
from playwright.async_api import async_playwright
import time
# --- CONFIG ---
GAME_URL = "https://f1-contest.com/versions/th/lazada/en.html"
WINDOW_NAME = "LEGO® - Chromium"

class LEGOF1Env(gym.Env):
    def __init__(self):
        super().__init__()
        self.off_track_count = 0  # Counter for crash detection
        self.step_count = 0
        self.max_steps = 600  # Timeout: end episode after 600 steps (~30s)
        super().__init__()
        self.observation_space = spaces.Box(low=0, high=255, shape=(84, 84, 1), dtype=np.uint8)
        self.action_space = spaces.Discrete(3)  # 0=left, 1=none, 2=right
        self.sct = mss.mss()
        self.page = None
        self.browser = None
        self.pw = None
        self.monitor = None

    def attach_browser(self, pw, browser, page):
        self.pw = pw
        self.browser = browser
        self.page = page
        self.monitor = self._get_client_area(WINDOW_NAME)

    def _click_red_bull_card(self):
        monitor = self._get_client_area(WINDOW_NAME)
        x = monitor['left'] + 865
        y = monitor['top'] + 700
        pyautogui.moveTo(x, y, duration=0.4)
        pyautogui.click()

    def _get_client_area(self, window_name):
        hwnd = win32gui.FindWindow(None, window_name)
        left, top = win32gui.ClientToScreen(hwnd, (0, 0))
        right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])
        return {'left': left, 'top': top, 'width': right - left, 'height': bottom - top}

    def _get_frame(self):
        img = self.sct.grab(self.monitor)
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        roi = frame[cy-100:cy, cx-50:cx+50]  # New ROI: width 100, height 100, above center
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        resized = cv2.resize(binary, (84, 84))
        return np.expand_dims(resized, axis=-1)

    def _reward(self, frame):
        white_pixels = np.count_nonzero(frame > 200)
        mid_y, mid_x = frame.shape[0] // 2, frame.shape[1] // 2
        self._last_reward_pixel = frame[mid_y, mid_x]
        self._last_white_pixel_count = white_pixels  # For debugging
        return 1 if white_pixels > 10 else -1

    def step(self, action):
        # Check if race has finished (removed async query_selector logic — will be handled in evaluation loop)
        # This avoids coroutine not awaited warning
        # Removed: query_selector use inside sync step()
        # (No-op section removed)
        if action == 0:
            keyboard.press('left')
            keyboard.release('right')
        elif action == 2:
            keyboard.press('right')
            keyboard.release('left')
        else:
            keyboard.release('left')
            keyboard.release('right')

        time.sleep(0.01)
        obs = self._get_frame()
        reward = self._reward(obs[:, :, 0])
        if reward == -1:
            self.off_track_count += 1
        else:
            self.off_track_count = 0
        terminated = self.off_track_count >= 10  # If off-track for 10 frames, assume crash
        self.step_count += 1
        truncated = self.step_count >= self.max_steps  # Timeout condition
        info = {}
        return obs, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        self.off_track_count = 0  # Reset crash counter
        self.step_count = 0
        obs = self._get_frame()
        return obs, {}

    def render(self):
        frame = self._get_frame()
        # Draw center pixel marker
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        frame_color = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        color = (0, 255, 0) if hasattr(self, '_last_reward_pixel') and self._last_reward_pixel > 200 else (0, 0, 255)
        cv2.circle(frame_color, (cx, cy), 3, color, -1)
        # cv2.imwrite("ai_view_last_frame.png", frame)  # Optional: save last view to file  # Save last view to file
        cv2.putText(frame_color, f"White pixels: {getattr(self, '_last_white_pixel_count', '?')}", (5, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.imshow("AI View", frame_color)
        cv2.waitKey(1)

    def close(self):
        cv2.destroyAllWindows()

# --- Async Browser Setup ---
async def setup_browser(env):
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False, args=["--window-size=1280,800"])
    page = await browser.new_page()
    await page.goto(GAME_URL)
    await page.click("button.cta-button.cta-button--normal")
    await page.keyboard.type("2001")
    await asyncio.sleep(1)

    monitor = env.env._get_client_area(WINDOW_NAME)
    x = monitor['left'] + 865
    y = monitor['top'] + 700
    pyautogui.moveTo(x, y, duration=0.4)
    pyautogui.click()

    await page.click("button.cta-button.cta-button--normal")
    await page.wait_for_selector(".game__ui__stats__text--time", timeout=30000)
    while True:
        timer = await page.inner_text(".game__ui__stats__text--time")
        if timer.strip().startswith("0:00"):
            break
        await asyncio.sleep(0.05)

    env.env.attach_browser(pw, browser, page)
# --- Training & Evaluation Entry Point ---
async def safe_shutdown(env):
    try:
        if env.env.browser:
            await env.env.browser.close()
    except Exception as e:
        print(f"[!] Browser close failed: {e}")
    try:
        if env.env.pw:
            await env.env.pw.stop()
    except Exception as e:
        print(f"[!] Playwright stop failed: {e}")

async def run_evaluation(env, model):
    print("[✓] Starting evaluation with trained model...")
    finish_count = 0
    crash_count = 0
    timeout_count = 0
    total_steps = 0
    obs, _ = env.reset()
    for _ in range(1000):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        total_steps += 1
        env.render()
        try:
            result_element = await env.env.page.query_selector("#application > div.page.score > div > div.score__result > div.score__result__box > div.score__result__box__time")
            if result_element:
                result_text = await result_element.inner_text()
                info["reason"] = "finished"
                info["time"] = result_text
        except:
            pass
        if terminated or truncated:
            with open("race_times.txt", "a", encoding="utf-8") as f:
                if info.get("reason") == "finished" and "time" in info:
                    f.write(f"[✓] Finished in: {info['time']}")
                    finish_count += 1
                elif info.get("reason") == "crash" or reward == -1:
                    f.write("[✗] Crashed or off-track")
                    crash_count += 1
                elif truncated:
                    f.write("[⏱] Timeout reached")
                    timeout_count += 1
            print("[⏱] Timeout reached or other end condition triggered")
            break
    print(f"Summary: Finished={finish_count}, Crashed={crash_count}, Timeout={timeout_count}, Steps={total_steps}")

async def main():
    from stable_baselines3.common.monitor import Monitor
    env = Monitor(LEGOF1Env())
    await setup_browser(env)
    model = DQN("CnnPolicy", env, verbose=1, buffer_size=1000, learning_starts=100,
                train_freq=1, target_update_interval=500)
    model.learn(total_timesteps=2000, callback=lambda _locals, _globals: env.render() or True)
    model.save("lego_f1_dqn")
    await safe_shutdown(env)
    env.close()
    await run_evaluation(env, model)

if __name__ == "__main__":
    asyncio.run(main())  # Cleaned: evaluation logic runs only once
