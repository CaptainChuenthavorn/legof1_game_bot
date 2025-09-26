import cv2
import numpy as np

def nothing(x):
    pass

# Load your image (replace this with a screen frame from your game)
frame = cv2.imread("start.png")

h, w, _ = frame.shape
region = frame

cv2.namedWindow("Track Mask")

# Create trackbars for HSV ranges
cv2.createTrackbar("H min", "Track Mask", 0, 180, nothing)
cv2.createTrackbar("H max", "Track Mask", 180, 180, nothing)
cv2.createTrackbar("S min", "Track Mask", 0, 255, nothing)
cv2.createTrackbar("S max", "Track Mask", 50, 255, nothing)
cv2.createTrackbar("V min", "Track Mask", 50, 255, nothing)
cv2.createTrackbar("V max", "Track Mask", 220, 255, nothing)

while True:
    # Read HSV values from trackbars
    h_min = cv2.getTrackbarPos("H min", "Track Mask")
    h_max = cv2.getTrackbarPos("H max", "Track Mask")
    s_min = cv2.getTrackbarPos("S min", "Track Mask")
    s_max = cv2.getTrackbarPos("S max", "Track Mask")
    v_min = cv2.getTrackbarPos("V min", "Track Mask")
    v_max = cv2.getTrackbarPos("V max", "Track Mask")

    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lower, upper)

    gray_ratio = np.sum(mask > 0) / mask.size
    print(f"Gray ratio: {gray_ratio:.2f}")

    cv2.imshow("Track Region", region)
    cv2.imshow("Track Mask", mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
