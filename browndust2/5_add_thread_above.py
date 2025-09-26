import cv2
import numpy as np
import mss
import win32gui
import pyautogui
import threading
import queue

# ---------------- Thread-safe click queue ----------------
click_queue = queue.Queue()

def click_worker():
    """Runs in background thread and handles mouse clicks separately."""
    while True:
        pos = click_queue.get()
        if pos is None:  # poison pill to exit thread
            break

        x, y = pos
        pyautogui.moveTo(x, y)
        pyautogui.click()
        click_queue.task_done()

# Start worker thread
threading.Thread(target=click_worker, daemon=True).start()

# ---------------------------------------------------------
def get_client_area(window_name):
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

def color_in_range(pixel, targets, tolerance=10):
    """Check if pixel matches any of the target color rules."""
    for target in targets:
        match = True
        for p, t in zip(pixel, target):
            if t is not None and abs(int(p) - int(t)) > tolerance:
                match = False
                break
        if match:
            return True
    return False

def capture_window_realtime(window_name):
    monitor = get_client_area(window_name)
    with mss.mss() as sct:
        print("Capturing client area only. Press 'q' to quit.")

        # Detection points and corresponding mouse move positions
        points = [(1270, 450), (270, 450)]
        point_mouse_move = [(1415, 650), (118, 650)]

        target_colors = [
            (31, 206, 253),
            (30, 203, 253),
            (86,222,235)
        ]
        tolerance = 10

        while True:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            for i, (x, y) in enumerate(points):
                if y < frame.shape[0] and x < frame.shape[1]:
                    pixel_bgr = frame[y, x].tolist()
                    pixel_rgb = (pixel_bgr[2], pixel_bgr[1], pixel_bgr[0])  # RGB

                    if color_in_range(pixel_rgb, target_colors, tolerance):
                        # Map detected point to corresponding mouse move position
                        move_x, move_y = point_mouse_move[i]
                        screen_x = move_x + monitor['left']
                        screen_y = move_y + monitor['top']

                        print(f"✅ Color match at {x},{y}: {pixel_rgb} → moving/clicking at ({screen_x},{screen_y})")
                        click_queue.put((screen_x, screen_y))

                    # Draw detection marker
                    cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
                    box_x1, box_y1 = x - 25, y - 100 - 25
                    box_x2, box_y2 = x + 25, y - 100 + 25
                    box_x1, box_y1 = max(0, box_x1), max(0, box_y1)
                    box_x2, box_y2 = min(frame.shape[1]-1, box_x2), min(frame.shape[0]-1, box_y2)
                    cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), pixel_bgr, -1)
                    cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (255, 255, 255), 2)
                    cv2.putText(frame, f"{pixel_rgb}", (box_x1, box_y1 - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

            cv2.imshow("Window Capture", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Stop worker thread
    click_queue.put(None)
    cv2.destroyAllWindows()

window_name = "BROWNDUST II"
capture_window_realtime(window_name)
