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

try:
    print("=== Automated Mouse & Keyboard Script Started ===")
    print("Press Ctrl+C in this terminal to stop the script.\n")

    while True:
        # Move to top area and click
        pyautogui.moveTo(2200, 290)
        print("[INFO] Moving mouse to (2200, 290) and clicking.")
        click_mouse()
        time.sleep(2)

        # Press the letter 'f'
        keyboard_controller.press('f')
        keyboard_controller.release('f')
        print("[INFO] Pressed and released key: 'f'")
        time.sleep(2)
        # pyautogui.moveTo(1870, 1120)
        # print("[INFO] Moving mouse to (1400, 830) and clicking.")
        # click_mouse()


        # Press F2 key
        keyboard_controller.press(Key.f2)
        keyboard_controller.release(Key.f2)
        print("[INFO] Pressed and released key: F2")
        time.sleep(2)

        # Click at multiple positions in sequence
        pyautogui.moveTo(1400, 830)
        print("[INFO] Moving mouse to (1400, 830) and clicking.")
        click_mouse()

        pyautogui.moveTo(1400, 1020)
        print("[INFO] Moving mouse to (1400, 1020) and clicking.")
        click_mouse()
        time.sleep(2)

        # Move to bottom area and click
        pyautogui.moveTo(2200, 1245)
        print("[INFO] Moving mouse to (2200, 1245) and clicking.")
        click_mouse()
        time.sleep(2)

        print("---- One full cycle completed. Restarting cycle in 2 seconds ----\n")

except KeyboardInterrupt:
    print("\n=== Program stopped by user. Exiting safely. ===")
