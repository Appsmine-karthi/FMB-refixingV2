import cv2
import numpy as np

# Define the line segments
segments = [
    [[678, 1251], [1590, 1221]],
    [[1590, 1221], [1544, 1298]],
    [[1515, 2225], [782, 2226]],
    [[782, 2226], [782, 1833]],
    [[782, 1833], [727, 1830]],
    [[1544, 1298], [1563, 1585]],
    [[1563, 1585], [1563, 1596]],
    [[1563, 1596], [1549, 1790]],
    [[1549, 1790], [1515, 2225]],
    [[727, 1830], [721, 1765]],
    [[721, 1765], [701, 1520]],
    [[701, 1520], [678, 1251]]
]
# Define the label data as a list of tuples: (position, text)
labels = [
    ((678, 1251), "A"),
    ((701, 1520), "23"),
    ((721, 1765), "22"),
    ((727, 1830), "1"),
    ((782, 1833), "2"),
    ((782, 2226), "D"),
    ((1515, 2225), "C"),
    ((1544, 1298), "3"),
    ((1549, 1790), "21"),
    ((1563, 1585), "20"),
    ((1563, 1596), "4"),
    ((1590, 1221), "B"),
]

# Create a blank canvas
canvas = np.ones((2500, 2000, 3), dtype=np.uint8) * 255

# Draw the text labels on the canvas
for (x, y), text in labels:
    cv2.putText(
        canvas,
        str(text),
        (x, y),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=2,
        color=(0, 128, 0),
        thickness=4,
        lineType=cv2.LINE_AA
    )



# Draw the lines
for seg in segments:
    pt1, pt2 = tuple(seg[0]), tuple(seg[1])
    cv2.line(canvas, pt1, pt2, color=(0, 0, 255), thickness=3)

# Display the image
cv2.imshow("Polyline", canvas)
cv2.waitKey(0)
cv2.destroyAllWindows()
