import cv2
import numpy as np

# Define the line segments
segments = [
    [[28, 28], [28, 3342]],
    [[28, 3342], [2355, 3342]],
    [[2355, 3342], [2355, 28]],
    [[2355, 28], [28, 28]],
    [[2355, 140], [28, 140]]
]


# Draw the coordinate text for each unique point


# Define the label data as a list of tuples: (position, text)
labels = [
    ((29, 78), "A"),
    ((941, 48), "B"),
    ((895, 125), "3"),
    ((133, 660), "2"),
    ((914, 412), "20"),
    ((914, 423), "4"),
    ((900, 617), "21"),
    ((72, 592), "22"),
    ((52, 347), "23"),
    ((90, 631), "1"),
    ((866, 1052), "C"),
    ((133, 1053), "D"),
]

# Create a blank canvas
canvas = np.ones((2500, 2000, 3), dtype=np.uint8) * 255

# Draw the text labels on the canvas
# for (x, y), text in labels:
#     cv2.putText(
#         canvas,
#         str(text),
#         (x, y),
#         fontFace=cv2.FONT_HERSHEY_SIMPLEX,
#         fontScale=2,
#         color=(0, 128, 0),
#         thickness=4,
#         lineType=cv2.LINE_AA
#     )

# drawn_points = set()
# for seg in segments:
#     for pt in seg:
#         pt_tuple = tuple(pt)
#         if pt_tuple not in drawn_points:
#             cv2.putText(
#                 canvas,
#                 f"{pt_tuple}",
#                 pt_tuple,
#                 fontFace=cv2.FONT_HERSHEY_SIMPLEX,
#                 fontScale=1.2,
#                 color=(0, 128, 0),
#                 thickness=3,
#                 lineType=cv2.LINE_AA
#             )
#             drawn_points.add(pt_tuple)


# Draw the lines
for seg in segments:
    pt1, pt2 = tuple(seg[0]), tuple(seg[1])
    cv2.line(canvas, pt1, pt2, color=(0, 0, 255), thickness=3)

# Display the image
# cv2.imshow("Polyline", canvas)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

cv2.imwrite("canvas.png", canvas)