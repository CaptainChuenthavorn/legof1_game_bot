#DQN Training Script
import gymnasium as gym
from gymnasium import spaces

import numpy as np
import cv2
import mss
import time
import keyboard
import pyautogui
import win32gui
from stable_baselines3 import DQN
from stable_baselines3.common.env_checker import check_env
from playwright.sync_api import sync_playwright

# --- ENVIRONMENT ---
class LEGOF1Env(gym.Env):
    def __init__(self, url="https://f1-contest.com/versions/th/lazada/en.html"):
        super().__init__()
        self.url = url
        self.window_name = "LEGO® - Chromium"
        self.monitor = None
        self.browser = None
        self.page = None
        self.sct = mss.mss()

        self.observation_space = spaces.Box(low=0, high=255, shape=(84, 84, 1), dtype=np.uint8)
        self.action_space = spaces.Discrete(3)  # 0=left, 1=none, 2=right

        self._launch_browser()

    def _launch_browser(self):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=False, args=["--window-size=1280,800"])
        self.page = self.browser.new_page()
        self.page.goto(self.url)

        self.page.wait_for_selector("button.cta-button.cta-button--normal")
        self.page.click("button.cta-button.cta-button--normal")
        self.page.keyboard.type("2001")
        time.sleep(1)
        self._click_red_bull_card()

        self.page.wait_for_selector("button.cta-button.cta-button--normal")
        self.page.click("button.cta-button.cta-button--normal")

        self.page.wait_for_selector(".game__ui__stats__text--time", timeout=30000)
        while True:
            timer = self.page.inner_text(".game__ui__stats__text--time").strip()
            if timer.startswith("0:00"):
                break
            time.sleep(0.05)

        self.monitor = self._get_client_area(self.window_name)

    def _click_red_bull_card(self):
        monitor = self._get_client_area(self.window_name)
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
        roi = frame[cy:cy+277, cx-75:cx+75]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (84, 84))
        return np.expand_dims(resized, axis=-1)

    def _reward(self, frame):
        mid_y, mid_x = frame.shape[0]//2, frame.shape[1]//2
        return 1 if frame[mid_y, mid_x] > 200 else -1

    def step(self, action):
        if action == 0:
            keyboard.press('left')
            keyboard.release('right')
        elif action == 2:
            keyboard.press('right')
            keyboard.release('left')
        else:
            keyboard.release('left')
            keyboard.release('right')

        time.sleep(0.05)
        obs = self._get_frame()
        reward = self._reward(obs[:, :, 0])
        terminated = False  # not implemented yet
        truncated = False
        info = {}

        return obs, reward, terminated, truncated, info


    def reset(self, seed=None, options=None):
        self.page.reload()
        time.sleep(2)
        self._launch_browser()
        obs = self._get_frame()
        return obs, {}


    def render(self, mode="human"):
        frame = self._get_frame()
        cv2.imshow("AI View", frame)
        cv2.waitKey(1)

    def close(self):
        if self.browser:
            self.browser.close()
        if self.p:
            self.p.stop()
        cv2.destroyAllWindows()

# --- TRAINING ---
if __name__ == "__main__":
    env = LEGOF1Env()
    check_env(env, warn=True)

    model = DQN("CnnPolicy", env, verbose=1, buffer_size=1000, learning_starts=100, train_freq=1, target_update_interval=500)
    model.learn(total_timesteps=2000)

    model.save("lego_f1_dqn")
    env.close()
