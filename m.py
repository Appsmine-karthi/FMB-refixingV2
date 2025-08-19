import cv2
import numpy as np

# Define the line segments
segments = [
    [[int(723.0), int(2018.0)], [int(814.0), int(2066.0)]],
    [[int(814.0), int(2066.0)], [int(1009.0), int(2067.0)]],
    [[int(1009.0), int(2067.0)], [int(1081.0), int(2097.0)]],
    [[int(1622.0), int(2075.0)], [int(1841.0), int(2019.0)]],
    [[int(1841.0), int(2019.0)], [int(1817.0), int(1789.0)]],
    [[int(1803.0), int(1539.0)], [int(1769.0), int(1312.0)]],
    [[int(1769.0), int(1312.0)], [int(693.0), int(1254.0)]],
    [[int(693.0), int(1254.0)], [int(675.0), int(1266.0)]],
    [[int(723.0), int(2018.0)], [int(693.0), int(2019.0)]],
    [[int(1841.0), int(2019.0)], [int(1871.0), int(2019.0)]],
    [[int(1769.0), int(1312.0)], [int(1769.0), int(1282.0)]],
    [[int(1769.0), int(1312.0)], [int(1799.0), int(1312.0)]],
    [[int(675.0), int(1266.0)], [int(645.0), int(1266.0)]],
    [[int(1081.0), int(2097.0)], [int(1224.0), int(2091.0)]],
    [[int(1224.0), int(2091.0)], [int(1622.0), int(2075.0)]],
    [[int(1811.0), int(1686.0)], [int(1803.0), int(1539.0)]],
    [[int(1817.0), int(1789.0)], [int(1817.0), int(1785.0)]],
    [[int(1817.0), int(1785.0)], [int(1811.0), int(1686.0)]],
    [[int(675.0), int(1266.0)], [int(699.0), int(1642.0)]],
    [[int(699.0), int(1642.0)], [int(723.0), int(2018.0)]],
    [[int(28.0), int(3342.0)], [int(28.0), int(28.0)]],
    [[int(28.0), int(28.0)], [int(2355.0), int(28.0)]],
    [[int(2355.0), int(28.0)], [int(2355.0), int(3342.0)]],
    [[int(2355.0), int(3342.0)], [int(28.0), int(3342.0)]],
    [[int(2355.0), int(3222.0)], [int(28.0), int(3222.0)]],
]
def DrawReference(segments):
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