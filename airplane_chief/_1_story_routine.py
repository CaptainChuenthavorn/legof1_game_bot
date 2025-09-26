import pyautogui
import time
import ctypes
import random
from pynput.keyboard import Controller, Key

# ---------------- Mouse Click (SendInput) ---------------- #
PUL = ctypes.POINTER(ctypes.c_ulong)

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

class INPUT_I(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", INPUT_I)]

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
INPUT_MOUSE = 0


import cv2
import numpy as np
import mss
import win32gui
import time
def countdown_message(seconds=3, task_description="Countdown "):
    for i in range(seconds, 0, -1):
        print(f"🕒 {task_description} in {i} second{'s' if i > 1 else ''}...")
        time.sleep(1)
def get_client_area(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd == 0:
        raise Exception(f"Window '{window_name}' not found!")
    win32gui.SetForegroundWindow(hwnd)
    # Get client area size
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])

    return {
        'left': left,
        'top': top,
        'width': right - left,
        'height': bottom - top
    }

def capture_window_realtime(window_name):
    monitor = get_client_area(window_name)

    # with mss.mss() as sct:
    #     print("Capturing client area only. Press 'q' to quit.")
    #     while True:
    #         img = sct.grab(monitor)
    #         frame = np.array(img)
    #         frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    #         cv2.imshow("Window Capture", frame)
    #         if cv2.waitKey(1) & 0xFF == ord('q'):
    #             break

    cv2.destroyAllWindows()


def click_mouse():
    """Simulates a left mouse click using SendInput."""
    extra = ctypes.c_ulong(0)
    ii_ = INPUT_I()
    ii_.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
    x = INPUT(type=INPUT_MOUSE, ii=ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
    time.sleep(random.uniform(0.01, 0.05))
    ii_.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
    x = INPUT(type=INPUT_MOUSE, ii=ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

keyboard_controller = Controller()

# 🔁 Replace with the actual title of your window
window_name = "Airplane Chefs - Cooking Game - cphero"
# capture_window_realtime(monitor)

monitor = get_client_area(window_name)
try:
    print("=== Automated Mouse & Keyboard Script Started ===")
    print("Press Ctrl+C in this terminal to stop the script.\n")

    while True:
        # Move to top area and click
        # move_x, move_y = point_mouse_move[i]
        #     screen_x = move_x + monitor['left']
        #     screen_y = move_y + monitor['top']
        
        countdown_message(3,"[INFO] Moving mouse to optn shop and clicking.")
        pyautogui.moveTo(105 + monitor['left'], 658+ monitor['top'],0.3)
        click_mouse()
        countdown_message(2,"[INFO] Moving mouse to get free fuel and clicking.")
        #fuel 205
        #gold 450
        pyautogui.moveTo(450 + monitor['left'], 590+ monitor['top'],0.3)
        click_mouse()
        
        countdown_message(39,"[INFO] Moving mouse to close top left and clicking.")
        pyautogui.moveTo(26 + monitor['left'], 26+ monitor['top'],0.5)
        click_mouse()
        countdown_message(1,"[INFO] Moving mouse to close top left and clicking.")
        pyautogui.moveTo(477 + monitor['left'], 26+ monitor['top'],0.5)
        click_mouse()
        time.sleep(0.3)
        click_mouse()
        countdown_message(2,"[INFO] Moving mouse to close top middle right and clicking.")
        pyautogui.moveTo(846 + monitor['left'], 26+ monitor['top'],0.5)
        click_mouse()
        time.sleep(0.3)
        click_mouse()
        countdown_message(2,"[INFO] Moving mouse to close top right and clicking.")
        pyautogui.moveTo(1300 + monitor['left'], 18+ monitor['top'],1)
        click_mouse()
        # pyautogui.moveTo(1284 + monitor['left'], 34+ monitor['top'],0.5)
        # click_mouse()

        pyautogui.moveTo(-100 + monitor['left'], 0+ monitor['top'],0.5)
        click_mouse()
        keyboard_controller.press(Key.ctrl_l)
        keyboard_controller.press('w')
        keyboard_controller.release(Key.ctrl_l)
        keyboard_controller.release('w')
        print('closing ctrl+w')
        time.sleep(0.3)
        monitor = get_client_area(window_name)
        countdown_message(2,"[INFO] Moving mouse to Ok recieve fuel and clicking.")
        
        pyautogui.moveTo(662 + monitor['left'], 642+ monitor['top'],1)
        click_mouse()
        time.sleep(0.3)
        click_mouse()
        countdown_message(2,"[INFO] Moving mouse to close top right and clicking.")
        pyautogui.moveTo(1200 + monitor['left'], 28+ monitor['top'],1)
        click_mouse()
        # # Press the letter 'f'
        # keyboard_controller.press('f')
        # keyboard_controller.release('f')
        # print("[INFO] Pressed and released key: 'f'")
        # time.sleep(2)

        # # Press F2 key
        # keyboard_controller.press(Key.f2)
        # keyboard_controller.release(Key.f2)
        # print("[INFO] Pressed and released key: F2")
        # time.sleep(2)

        # # Click at multiple positions in sequence
        # pyautogui.moveTo(1400, 830)
        # print("[INFO] Moving mouse to (1400, 830) and clicking.")
        # click_mouse()

        # pyautogui.moveTo(1400, 1020)
        # print("[INFO] Moving mouse to (1400, 1020) and clicking.")
        # click_mouse()
        # time.sleep(2)

        # # Move to bottom area and click
        # pyautogui.moveTo(2200, 1245)
        # print("[INFO] Moving mouse to (2200, 1245) and clicking.")
        # click_mouse()
        # time.sleep(2)

        # print("---- One full cycle completed. Restarting cycle in 2 seconds ----\n")

except KeyboardInterrupt:
    print("\n=== Program stopped by user. Exiting safely. ===")
