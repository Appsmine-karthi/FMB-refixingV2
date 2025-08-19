import cv2
import numpy as np
import json

def DrawReference_(data):
    data = json.loads(data)
    segments = data["line1"] + data["line3"]
    canvas = np.ones((2500, 2000, 3), dtype=np.uint8) * 255
    drawn_points = set()
    for seg in segments:
        pt1, pt2 = tuple(seg[0]), tuple(seg[1])

        # Draw the line
        cv2.line(canvas, pt1, pt2, color=(0, 0, 255), thickness=3)

        # Label the points if we haven't already
        for pt in [pt1, pt2]:
            if pt not in drawn_points:
                # Draw a small circle at the point
                cv2.circle(canvas, pt, 5, color=(255, 0, 0), thickness=-1)

                # Add the coordinate label
                label_text = f"({pt[0]}, {pt[1]})"
                cv2.putText(
                    canvas,
                    label_text,
                    (pt[0] + 10, pt[1] - 10),  # Offset the text slightly from the point
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.6,
                    color=(0, 128, 0),
                    thickness=2,
                    lineType=cv2.LINE_AA
                )
                drawn_points.add(pt)

    cv2.imwrite("canvas.png", canvas)