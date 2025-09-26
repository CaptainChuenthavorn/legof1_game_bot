import cv2
import numpy as np
import mss
import win32gui
import pyautogui

def get_client_area(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd == 0:
        raise Exception(f"Window '{window_name}' not found!")

    # Get client area size
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])
    return {
        'left': left, 
        'top': top+200,
        'width': 1,
        'height': 1
    }

def color_in_range(pixel, targets, tolerance=10):
    """Check if pixel matches any of the target color rules."""
    for target in targets:
        # Case 1: Full RGB target (all channels matter)
        if None not in target:
            if all(abs(int(p) - int(t)) <= tolerance for p, t in zip(pixel, target)):
                return True

        # Case 2: Flexible target (some channels ignored -> marked as None)
        else:
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
        while True:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            # 🎯 Target colors (None means "don’t care")
            target_colors = [
                (99, 219, 100),      # Exact RGB
            ]
            tolerance = 10

            # 📌 Detection points
            points = [(0, 0)]
            for (x, y) in points:
                if y < frame.shape[0] and x < frame.shape[1]:
                    pixel_bgr = frame[y, x].tolist()
                    pixel_rgb = (pixel_bgr[2], pixel_bgr[1], pixel_bgr[0])  # RGB

                    # ✅ Check color match
                    if color_in_range(pixel_rgb, target_colors, tolerance):
                        screen_x = x + monitor['left']
                        screen_y = y + monitor['top']

                        print(f"✅ Color match at {x},{y}: {pixel_rgb} → clicking at ({screen_x},{screen_y})")

                        pyautogui.moveTo(screen_x, screen_y)
                        pyautogui.click()
                        break

                    # 🔴 Draw a marker on the exact pixel
            #         cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)

            #         # 🎨 Draw a color preview box above the point
            #         box_x1, box_y1 = x - 25, y - 100 - 25
            #         box_x2, box_y2 = x + 25, y - 100 + 25

            #         box_x1, box_y1 = max(0, box_x1), max(0, box_y1)
            #         box_x2, box_y2 = min(frame.shape[1]-1, box_x2), min(frame.shape[0]-1, box_y2)

            #         color_fill = (int(pixel_bgr[0]), int(pixel_bgr[1]), int(pixel_bgr[2]))
            #         cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), color_fill, -1)
            #         cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (255, 255, 255), 2)

            #         cv2.putText(frame, f"{pixel_rgb}", (box_x1,box_y1 -20),
            #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

            # # 🔴 Draw static reference rectangles
            # cv2.rectangle(frame, (48, 716), (179, 838), (0, 0, 255), 2)
            # cv2.rectangle(frame, (1362, 733), (1482, 847), (0, 0, 255), 2)

            # cv2.imshow("Window Capture", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

# 🔁 Replace with the actual title of your window
window_name = "Human Benchmark - Reaction Time Test - Google Chrome"
capture_window_realtime(window_name)
