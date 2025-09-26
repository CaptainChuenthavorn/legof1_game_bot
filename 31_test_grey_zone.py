import cv2
import numpy as np

def is_on_track(obs):
    h, w, _ = obs.shape
    # region = obs[h-200:h-100, w//2-50:w//2+50]
    region = obs
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    lower_gray = np.array([81, 0, 99])
    upper_gray = np.array([180, 56, 255])
    mask = cv2.inRange(hsv, lower_gray, upper_gray)
    gray_ratio = np.sum(mask > 0) / mask.size

    cv2.imshow("Track Region", region)
    cv2.imshow("Gray Mask", mask)
    print(f"Gray ratio: {gray_ratio:.2f} — On Track: {gray_ratio > 0.5}")

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return gray_ratio > 0.5

# Load the uploaded image
image = cv2.imread("start.png")
is_on_track(image)