import gym
from gym import spaces
import numpy as np
import pyautogui
import win32gui
import keyboard
import time
import cv2
import mss
import threading
from playwright.sync_api import sync_playwright

class LegoF1Env(gym.Env):
    def __init__(self):
        super(LegoF1Env, self).__init__()
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False, args=["--window-size=1280,800"])
        self.page = self.browser.new_page()
        self.page.goto("https://f1-contest.com/versions/th/lazada/en.html")
        
        self.window_title = "LEGO® - Chromium"
        self.capture_thread = None
        self.stop_event = threading.Event()
        self.monitor = self.get_client_area(self.window_title)

        
        # self._setup_game()

        # Define action and observation spaces
        self.action_space = spaces.Discrete(2)  # 0 = no action, 1 = press right
        self.observation_space = spaces.Box(low=0, high=255, shape=(self.monitor['height'], self.monitor['width'], 3), dtype=np.uint8)

    def get_client_area(self, window_name):
        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd == 0:
            raise Exception(f"Window '{window_name}' not found!")
        left, top = win32gui.ClientToScreen(hwnd, (0, 0))
        right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])
        return {'left': left, 'top': top, 'width': right - left, 'height': bottom - top}

    def _setup_game(self):
        print("[*] Setting up game...")
        self.page.wait_for_selector("button.cta-button.cta-button--normal")
        self.page.click("button.cta-button.cta-button--normal")
        time.sleep(1)
        self.page.keyboard.type("2001")
        time.sleep(1)
        self.click_red_bull_card()
        time.sleep(1)
        self.page.wait_for_selector("button.cta-button.cta-button--normal")
        self.page.click("button.cta-button.cta-button--normal")

        self.page.wait_for_selector(".game__ui__stats__text--time", timeout=30000)
        while True:
            timer_text = self.page.inner_text(".game__ui__stats__text--time").strip()
            if timer_text.startswith("0:00"):
                break
            time.sleep(0.05)

    def click_red_bull_card(self):
        monitor = self.monitor
        x = monitor['left'] + 865
        y = monitor['top'] + 700
        pyautogui.moveTo(x, y, duration=0.4)
        pyautogui.click()

    def _capture_screen(self):
        with mss.mss() as sct:
            while not self.stop_event.is_set():
                img = sct.grab(self.monitor)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                self.last_frame = frame
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    def reset(self):
        self.page.reload()
        time.sleep(2)
        self._setup_game()
        self.last_frame = None
        self.stop_event.clear()
        self.capture_thread = threading.Thread(target=self._capture_screen, daemon=True)
        self.capture_thread.start()
        time.sleep(0.2)
        return self._get_observation()

    def _get_observation(self):
        return self.last_frame if self.last_frame is not None else np.zeros((self.monitor['height'], self.monitor['width'], 3), dtype=np.uint8)

    def step(self, action):
        if action == 1:
            keyboard.press('right')
        elif action == 2:
            keyboard.press('left')
        time.sleep(0.1)
        keyboard.release('right')
        keyboard.release('left')

        obs = self._get_observation()

        reward = self.compute_reward(obs)
        done = self.check_done(obs)

        return obs, reward, done, {}

    def compute_reward(self, obs):
        reward = 0

        if self.is_on_track(obs):
            reward += 1
        else:
            reward -= 1

        if self.score_increased():
            reward += 10

        if self.is_stuck():
            reward -= 10

        if self.reversed():
            reward -= 100

        if self.finished_fast():
            reward += 100

        return reward


    def close(self):
        self.stop_event.set()
        if self.capture_thread:
            self.capture_thread.join()
        self.browser.close()
        self.playwright.stop()
        cv2.destroyAllWindows()


    def is_on_track(self, obs):
        # Crop region where the car usually is
        h, w, _ = obs.shape
        # region = obs[h-200:h-100, w//2-50:w//2+50]  # bottom center slice
        region= obs
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        lower_gray = np.array([81, 0, 99])
        upper_gray = np.array([180, 56, 255])
        mask = cv2.inRange(hsv, lower_gray, upper_gray)
        gray_ratio = np.sum(mask > 0) / mask.size
        # return gray_ratio > 0.5  # threshold: adjust if needed
        return gray_ratio > 0.5, mask
    def is_stuck(self):
        now = time.time()
        if not hasattr(self, "pos_history"):
            self.pos_history = []
        self.pos_history.append((now, self.last_position))

        # Remove old entries (> 3 sec ago)
        self.pos_history = [(t, p) for t, p in self.pos_history if now - t <= 3]

        # Check position variance
        if len(self.pos_history) < 2:
            return False
        positions = [p for t, p in self.pos_history]
        x_vals = [p[0] for p in positions]
        y_vals = [p[1] for p in positions]
        if max(x_vals) - min(x_vals) < 5 and max(y_vals) - min(y_vals) < 5:
            return True
        return False


    def finished_fast(self):
        if not hasattr(self, "start_time"):
            return False
        elapsed = time.time() - self.start_time
        return self.race_done() and elapsed < 78

    def race_done(self):
        timer_text = self.page.inner_text(".game__ui__stats__text--time").strip()
        return not timer_text.startswith("0:00")
def get_edges(frame):
    h, w, _ = frame.shape
    region = frame

    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, threshold1=50, threshold2=150)

    return region, edges

# def test_is_on_track(env):
#     print("[*] Testing is_on_track() — Press 'q' to quit")
#     while True:
#         obs = env._get_observation()
#         if obs is None:
#             continue

#         # result = env.is_on_track(obs)
#         # print(f"On track: {result}")

#         # # Optional: visualize the detection region
#         # h, w, _ = obs.shape
#         # region = obs
#         # region = obs[h-200:h-100, w//2-50:w//2+50]


#         # _, mask = env.is_on_track(obs)

#         # # Optional: convert to BGR so it's not grayscale
#         # mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
#         # cv2.imshow("Window Capture", mask_bgr)
#         # region, edges = get_edges(frame)
#         # cv2.imshow("Track Region", region)
#         img = sct.grab(monitor)
#         frame = np.array(img)
#         frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

#         region, edges = get_edges(frame)

#         # Show both region and its edges
#         cv2.imshow("Track Region", region)
#         cv2.imshow("Edge Detection", edges)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cv2.destroyAllWindows()

def get_client_area(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd == 0:
        raise Exception(f"Window '{window_name}' not found!")

    # Get client area size
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])

    return {
        'left': left,
        'top': top,
        'width': right - left,
        'height': bottom - top
    }

# def is_on_track(frame):
#     h, w, _ = frame.shape
#     # region = frame[h-200:h-100, w//2-50:w//2+50]
#     region = frame
#     hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
#     lower_gray = np.array([81, 0, 99])
#     upper_gray = np.array([180, 56, 255])
#     mask = cv2.inRange(hsv, lower_gray, upper_gray)
#     gray_ratio = np.sum(mask > 0) / mask.size

#     cv2.imshow("Track Region", region)
#     cv2.imshow("Gray Mask", mask)
#     print(f"Gray ratio: {gray_ratio:.2f} — On Track: {gray_ratio > 0.5}")

#     return gray_ratio > 0.5


# def capture_window_realtime(window_name):
#     monitor = get_client_area(window_name)
#     with mss.mss() as sct:
#         while True:
#             img = sct.grab(monitor)
#             frame = np.array(img)
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

#             _, mask = is_on_track(frame)

#             # Optional: convert to BGR so it's not grayscale
#             mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
#             cv2.imshow("Window Capture", mask_bgr)

#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
#     cv2.destroyAllWindows()
def capture_window_realtime(window_name):
    monitor = get_client_area(window_name)
    with mss.mss() as sct:
        while True:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            region, edges = get_edges(frame)

            # Show both region and its edges
            cv2.imshow("Track Region", region)
            cv2.imshow("Edge Detection", edges)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    env = LegoF1Env()
    obs = env.reset()
    capture_window_realtime("LEGO® - Chromium")
    # test_is_on_track(env)
    # for episode in range(10000):
    #     obs = env.reset()
    #     total_reward = 0
    #     for step in range(780):
    #         action = env.action_space.sample()  # replace with your model later
    #         obs, reward, done, _ = env.step(action)
    #         total_reward += reward
    #         if done:
    #             break
    #     print(f"Episode {episode} — Total reward: {total_reward}")
    env.close()

