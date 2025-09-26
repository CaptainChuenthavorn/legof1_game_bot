import mss
import win32gui
import win32api
import win32con
import time

# -------------------------------
# Get client area of window
# -------------------------------
def get_client_area(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd == 0:
        raise Exception(f"Window '{window_name}' not found!")

    # Get client area rectangle (relative to screen coords)
    rect = win32gui.GetClientRect(hwnd)
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, (rect[2], rect[3]))

    # Capture only 1×1 pixel region (top+200 as in your code)
    return {
        'left': left,
        'top': top + 200,
        'width': 1,
        'height': 1
    }

# -------------------------------
# Fast color matcher
# -------------------------------
def color_in_range(pixel, targets, tolerance=10):
    for target in targets:
        match = True
        for p, t in zip(pixel, target):
            if t is not None and abs(int(p) - int(t)) > tolerance:
                match = False
                break
        if match:
            return True
    return False

# -------------------------------
# Super fast Win32 click
# -------------------------------
def fast_click(x, y):
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

# -------------------------------
# Main loop
# -------------------------------
def capture_window_realtime(window_name):
    monitor = get_client_area(window_name)
    target_colors = [(99, 219, 100)]  # target RGB
    tolerance = 10

    with mss.mss() as sct:
        print("Capturing client area. Press Ctrl+C to quit.")
        last = time.time()

        while True:
            img = sct.grab(monitor)

            # Get pixel at (0,0) → (R,G,B)
            pixel_bgr = img.pixel(0, 0)  # returns (B,G,R)
            pixel_rgb = (pixel_bgr[2], pixel_bgr[1], pixel_bgr[0])

            if color_in_range(pixel_rgb, target_colors, tolerance):
                screen_x = monitor['left']
                screen_y = monitor['top']
                print(f"✅ Color match {pixel_rgb} → clicking at ({screen_x},{screen_y})")
                fast_click(screen_x, screen_y)
                break

            # Debug FPS
            now = time.time()
            print(f"Loop: {(now - last) * 1000:.2f} ms")
            last = now


# 🔁 Replace with the actual window title
window_name = "Human Benchmark - Reaction Time Test - Google Chrome"
capture_window_realtime(window_name)
