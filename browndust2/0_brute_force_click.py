import ctypes
import time
import random
import win32api
import win32con
import win32gui
import math
import keyboard

# ---------------- Mouse Click (SendInput) ---------------- #
# This section defines the structures and functions needed to simulate
# mouse input using Windows' SendInput API. This method is generally
# more reliable than pyautogui for some applications.

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
    time.sleep(random.uniform(0.01, 0.05))  # Add a small random delay between down and up
    ii_.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
    x = INPUT(type=INPUT_MOUSE, ii=ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

# ---------------- Smooth Mouse Curve ---------------- #
# This section defines a function to move the mouse with a smooth,
# human-like curve instead of a straight line, which can be less detectable.

def move_mouse_smoothly_curve(to_x, to_y, duration=None):
    """
    Moves the mouse to a target position with a randomized, smooth curve.
    
    Args:
        to_x (int): The target X coordinate.
        to_y (int): The target Y coordinate.
        duration (float, optional): The duration of the movement in seconds.
                                    If None, a random duration is chosen.
    """
    from_x, from_y = win32api.GetCursorPos()
    if duration is None:
        duration = 0.01  # Shortened duration for a fast click bot
    steps = int(duration * 100)
    curve_mag = random.randint(10, 30)  # Reduced curve magnitude for precision
    curve_dir = random.choice([-1, 1])
    
    for i in range(steps + 1):
        t = i / steps
        ease = t * t * (3 - 2 * t)
        
        x = from_x + (to_x - from_x) * ease
        y = from_y + (to_y - from_y) * ease
        
        curve = curve_mag * math.sin(t * math.pi) * curve_dir
        
        if abs(to_x - from_x) > abs(to_y - from_y):
            y += curve
        else:
            x += curve
            
        win32api.SetCursorPos((int(x), int(y)))
        time.sleep(duration / steps)

# ---------------- Window Handling Logic ---------------- #
def get_client_area(window_name):
    """
    Finds a window by name and returns its client area coordinates.
    
    Args:
        window_name (str): The exact title of the window.

    Returns:
        dict: A dictionary containing 'left', 'top', 'width', and 'height'.
    """
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd == 0:
        raise Exception(f"Window '{window_name}' not found!")

    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])
    return {
        'left': left,
        'top': top,
        'width': right - left,
        'height': bottom - top
    }

# ---------------- Main Bot Logic ---------------- #
def run_continuous_click_bot():
    """
    Continuously moves the mouse between two points relative to a specific
    window and clicks, without any color detection.
    """
    window_name = "BROWNDUST II"
    
    try:
        monitor = get_client_area(window_name)
    except Exception as e:
        print(f"Error: {e}")
        print(f"Please make sure the '{window_name}' window is open.")
        return

    print("Continuous click bot started.")
    print(f"Targeting window '{window_name}' at screen coordinates: {monitor['left']},{monitor['top']}")
    print("Press 'q' to quit.")
    
    # These are the relative coordinates from the top-left of the client area
    point1_rel = (1415, 650)
    point2_rel = (118, 650)
    
    while True:
        # Calculate absolute screen coordinates for the first point
        screen_x1 = point1_rel[0] + monitor['left']
        screen_y1 = point1_rel[1] + monitor['top']
        
        # Move to the first point and click
        move_mouse_smoothly_curve(screen_x1, screen_y1)
        click_mouse()
        
        # Add a small random delay between clicks
        # time.sleep(random.uniform(0.05, 0.1))
        # time.sleep(0.01)
        # Calculate absolute screen coordinates for the second point
        screen_x2 = point2_rel[0] + monitor['left']
        screen_y2 = point2_rel[1] + monitor['top']

        # Move to the second point and click
        move_mouse_smoothly_curve(screen_x2, screen_y2)
        click_mouse()

        # Add another small random delay
        # time.sleep(0.01)

        # Check for the 'q' key to quit
        if keyboard.is_pressed('q'):
            print("Quitting bot.")
            break

if __name__ == "__main__":
    # Wait for a few seconds to give the user time to move the mouse
    # and focus on the game window.
    print("Starting bot in 3 seconds. Please make sure the target window is active.")
    time.sleep(3)
    run_continuous_click_bot()