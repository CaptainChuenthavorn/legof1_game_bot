import cv2
import numpy as np
import mss
import win32gui
import pyautogui
import threading
import queue
import ctypes
import time
import random
import math

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
    extra = ctypes.c_ulong(0)
    ii_ = INPUT_I()
    ii_.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
    x = INPUT(type=INPUT_MOUSE, ii=ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
    time.sleep(random.uniform(0.01, 0.05))
    ii_.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
    x = INPUT(type=INPUT_MOUSE, ii=ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

# ---------------- Thread-safe click queue ----------------
click_queue = queue.Queue()
def click_worker():
    while True:
        pos = click_queue.get()
        if pos is None:
            break
        x, y = pos
        pyautogui.moveTo(x, y)
        click_mouse()
        click_queue.task_done()
threading.Thread(target=click_worker, daemon=True).start()

# ---------------- Window utils ----------------
def get_client_area(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd == 0:
        raise Exception(f"Window '{window_name}' not found!")
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    rect = win32gui.GetClientRect(hwnd)
    right_bottom = win32gui.ClientToScreen(hwnd, (rect[2], rect[3]))
    left, top = left, top
    right, bottom = right_bottom
    return {
        'left': left,
        'top': top + 500,         # your original offset
        'width': right - left,
        'height': bottom - top - 500
    }

# ---------------- Color detection helpers ----------------
def hsv_mask_for_range(hsv_img, lower, upper):
    """Return binary mask for hsv_img in [lower, upper] (each is (h,s,v))."""
    lower = np.array(lower, dtype=np.uint8)
    upper = np.array(upper, dtype=np.uint8)
    mask = cv2.inRange(hsv_img, lower, upper)
    # morphological clean-up to reduce noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    return mask

import numpy as np
import cv2

def is_blue_roi(roi_hsv, roi_bgr,
                blue_sat_range=((90, 80, 80), (140, 255, 255)),
                pale_hue_range=(80, 160),  # allow purple->blue hue sweep
                pale_s_max=70, pale_v_min=180,
                b_dominance_margin=25,
                area_pct_threshold=0.12):
    """
    Return True if ROI likely contains the blue/purple->white->blue button.
    roi_hsv: HSV image slice for ROI (numpy array H,S,V)
    roi_bgr: BGR image slice for ROI (numpy array B,G,R)
    """

    # Protect empty ROI
    h, w = roi_hsv.shape[:2]
    total_pixels = max(1, h*w)

    # 1) Saturated blue mask (strict)
    lower = np.array(blue_sat_range[0], dtype=np.uint8)
    upper = np.array(blue_sat_range[1], dtype=np.uint8)
    mask_strict = cv2.inRange(roi_hsv, lower, upper)
    strict_frac = cv2.countNonZero(mask_strict) / total_pixels
    if strict_frac >= area_pct_threshold:
        return True

    # 2) Pale / white with blue tint:
    #    - low saturation (near white), high value, and hue in a broad range that includes purple->blue
    h_chan = roi_hsv[:,:,0].astype(int)
    s_chan = roi_hsv[:,:,1].astype(int)
    v_chan = roi_hsv[:,:,2].astype(int)

    # mask for low-saturation, high-value + hue near blue/purple
    mask_pale = ((s_chan <= pale_s_max) & (v_chan >= pale_v_min) &
                 ( (h_chan >= pale_hue_range[0]) & (h_chan <= pale_hue_range[1]) ))
    pale_frac = np.count_nonzero(mask_pale) / total_pixels
    if pale_frac >= area_pct_threshold * 0.6:  # pale can be less strict, use smaller multiplier
        return True

    # 3) B channel dominance in BGR (for very white frames with slight blue tint)
    #    Compare channel means: require mean(B) > mean(R,G) by margin
    mean_b = float(np.mean(roi_bgr[:,:,0]))
    mean_g = float(np.mean(roi_bgr[:,:,1]))
    mean_r = float(np.mean(roi_bgr[:,:,2]))
    if (mean_b - max(mean_r, mean_g)) >= b_dominance_margin and (mean_b >= 80):
        # require some absolute blue brightness too
        return True

    # Otherwise not detected
    return False
def sample_roi_stats(roi_hsv, roi_bgr):
    h_mean = np.mean(roi_hsv[:,:,0])
    s_mean = np.mean(roi_hsv[:,:,1])
    v_mean = np.mean(roi_hsv[:,:,2])
    b_mean = np.mean(roi_bgr[:,:,0])
    g_mean = np.mean(roi_bgr[:,:,1])
    r_mean = np.mean(roi_bgr[:,:,2])
    print(f"HSV mean: H={h_mean:.1f}, S={s_mean:.1f}, V={v_mean:.1f}")
    print(f"BGR mean: B={b_mean:.1f}, G={g_mean:.1f}, R={r_mean:.1f}")
# ---------------- Main capture & logic ----------------
def capture_window_realtime(window_name):
    monitor = get_client_area(window_name)
    with mss.mss() as sct:
        print("Capturing client area only. Press 'q' to quit.")

        # detection points (x,y) RELATIVE to client area (as you had)
        points = [(188, 77), (1338, 96)]
        # where to move & click on screen (relative to client area then add monitor offsets)
        point_mouse_move = [(188, 180),(1338, 200), ]

        # ---------- HSV color ranges (tune these) ----------
        # OpenCV Hue range is 0..179
        blue_lower = (90, 80, 80)    # start values for blue (H,S,V)
        blue_upper = (255, 255, 255)

        green_lower = (35, 60, 60)   # start values for green
        green_upper = (85, 255, 255)

        # ROI size around detection point (pixels)
        roi_radius = 14   # 29x29 region
        # percent of ROI pixels that must match to count as detection
        area_pct_threshold = 0.12   # 12% by default, tune upward if too noisy
        # require N consecutive frames to confirm detection/loss (debouncing)
        consecutive_on_required = 2
        consecutive_off_required = 2

        # per-point state:
        detect_on_counters = [0] * len(points)
        detect_off_counters = [0] * len(points)
        holding_state = [False] * len(points)     # True when we issued mouseDown for green
        last_click_time = [0.0] * len(points)
        click_cooldown = 0.18   # seconds between permitted clicks on same point

        while True:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            for i, (px, py) in enumerate(points):
                # safety clamp
                if py < 0 or px < 0 or py >= frame.shape[0] or px >= frame.shape[1]:
                    continue

                # ROI coordinates in frame space
                x1 = max(0, px - roi_radius)
                y1 = max(0, py - roi_radius)
                x2 = min(frame.shape[1]-1, px + roi_radius)
                y2 = min(frame.shape[0]-1, py + roi_radius)
                roi_hsv = hsv[y1:y2+1, x1:x2+1]

                # create masks
                mask_blue = hsv_mask_for_range(roi_hsv, blue_lower, blue_upper)
                mask_green = hsv_mask_for_range(roi_hsv, green_lower, green_upper)
                total_pixels = roi_hsv.shape[0] * roi_hsv.shape[1] if roi_hsv.size else 1

                blue_frac = (cv2.countNonZero(mask_blue) / total_pixels)
                green_frac = (cv2.countNonZero(mask_green) / total_pixels)

                # Choose detection based on fraction vs threshold
                # inside the main loop, after you compute roi_hsv (HSV slice) and roi_bgr (BGR slice)
                blue_detected = is_blue_roi(roi_hsv, frame[y1:y2+1, x1:x2+1], 
                                            blue_sat_range=((90,80,60),(140,255,255)),
                                            pale_hue_range=(70,165),
                                            pale_s_max=80, pale_v_min=160,
                                            b_dominance_margin=18,
                                            area_pct_threshold=0.12)

                green_detected = green_frac >= area_pct_threshold
                # sample_roi_stats(roi_hsv,  frame[y1:y2+1, x1:x2+1])
                # Debug overlay: box + fractions
                cv2.rectangle(frame, (x1, y1), (x2, y2), (200,200,200), 1)
                cv2.putText(frame, f"B:{blue_frac:.2f} G:{green_frac:.2f}",
                            (x1, max(0,y1-8)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,255), 1, cv2.LINE_AA)

                # ---------- handle green (hold) logic ----------
                if green_detected and not blue_detected:
                    detect_on_counters[i] += 1
                    detect_off_counters[i] = 0
                else:
                    detect_off_counters[i] += 1
                    detect_on_counters[i] = 0

                # Confirm green on
                if detect_on_counters[i] >= consecutive_on_required and not holding_state[i]:
                    # start holding: move to mapped screen coords and mouseDown
                    screen_x = point_mouse_move[i][0] + monitor['left']
                    screen_y = point_mouse_move[i][1] + monitor['top']
                    print(f"[HOLD START] Point {i} green detected -> mouseDown at ({screen_x},{screen_y})")
                    pyautogui.moveTo(screen_x, screen_y)
                    pyautogui.mouseDown()
                    holding_state[i] = True

                # Confirm green off (release)
                if detect_off_counters[i] >= consecutive_off_required and holding_state[i]:
                    screen_x = point_mouse_move[i][0] + monitor['left']
                    screen_y = point_mouse_move[i][1] + monitor['top']
                    print(f"[HOLD END] Point {i} green lost -> mouseUp at ({screen_x},{screen_y})")
                    pyautogui.moveTo(screen_x, screen_y)
                    pyautogui.mouseUp()
                    holding_state[i] = False

                # ---------- handle blue (quick click) logic ----------
                # Prefer blue click only if not currently holding for green at the same point
                current_time = time.time()
                if blue_detected and not holding_state[i]:
                    # debounce with consecutive frames
                    if detect_on_counters[i] >= consecutive_on_required:
                        if current_time - last_click_time[i] > click_cooldown:
                            move_x = point_mouse_move[i][0] + monitor['left']
                            move_y = point_mouse_move[i][1] + monitor['top']
                            print(f"[CLICK] Point {i} blue detected -> enqueue click at ({move_x},{move_y})")
                            click_queue.put((move_x, move_y))
                            last_click_time[i] = current_time
                            # reset counters to avoid repeated fast clicks without cooldown
                            detect_on_counters[i] = 0
                            detect_off_counters[i] = 0

                # Draw a colored indicator on big frame to show state
                center = (px, py)
                if holding_state[i]:
                    cv2.circle(frame, center, 8, (0,255,0), -1)   # green filled
                elif blue_detected:
                    cv2.circle(frame, center, 8, (255,0,0), -1)   # blue filled
                elif green_detected:
                    cv2.circle(frame, center, 8, (0,200,200), 2)  # pale indicator
                else:
                    cv2.circle(frame, center, 5, (0,0,255), 1)

            cv2.imshow("Window Capture", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Stop worker thread
    click_queue.put(None)
    cv2.destroyAllWindows()

# ---------------- Run ----------------
if __name__ == "__main__":
    window_name = "BROWNDUST II"
    try:
        capture_window_realtime(window_name)
    except Exception as e:
        print("Error:", e)
