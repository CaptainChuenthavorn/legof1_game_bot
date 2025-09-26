import cv2
import numpy as np

class RoadDetector:
    def __init__(self, template_path):
        self.template = cv2.imread(template_path, 0)  # Load in grayscale
        self.template_w = self.template.shape[1]
        self.template_h = self.template.shape[0]

    def detect(self, roi_gray):
        res = cv2.matchTemplate(roi_gray, self.template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        return max_val, max_loc

    def draw_result(self, roi_color, max_val, max_loc):
        threshold = 0.5
        if max_val >= threshold:
            top_left = max_loc
            bottom_right = (top_left[0] + self.template_w, top_left[1] + self.template_h)
            cv2.rectangle(roi_color, top_left, bottom_right, (0, 255, 0), 2)
            cv2.putText(roi_color, f"Match: {max_val:.2f}", (5, 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            cv2.putText(roi_color, f"No match ({max_val:.2f})", (5, 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        return roi_color

# Example usage
if __name__ == "__main__":
    frame = cv2.imread("sample_roi.png")
    gray_roi = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    detector = RoadDetector("ref_road.png")
    max_val, max_loc = detector.detect(gray_roi)
    result_img = detector.draw_result(frame.copy(), max_val, max_loc)

    cv2.imshow("Template Match", result_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
