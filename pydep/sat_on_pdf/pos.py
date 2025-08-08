import math
import numpy as np
def euc(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def cord_angle(p1, p2, p3):

    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    magnitude_v1 = math.sqrt(v1[0]**2 + v1[1]**2)
    magnitude_v2 = math.sqrt(v2[0]**2 + v2[1]**2)
    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return 0.0
    angle_radians = math.acos(dot_product / (magnitude_v1 * magnitude_v2))
    angle_degrees = math.degrees(angle_radians)
    
    return angle_degrees

def compute_angle(pts):
    arm=[
        # [34,56],
        # [67,67]
        # x,y
    ]

    point_tp = []
    point_elb = []
    point_bs = []

    if(euc(pts[0],pts[1]) > euc(pts[1],pts[2])):
        arm = [pts[0],pts[1]]
    else:
        arm = [pts[1],pts[2]]
    
    if(arm[0][1] > arm[1][1]):
        point_tp = arm[1]
        point_elb = arm[0]
        point_bs = [arm[0][0]+10,arm[0][1]]
    elif(arm[0][1] < arm[1][1]):
        point_tp = arm[0]
        point_elb = arm[1]
        point_bs = [arm[1][0]+10,arm[1][1]]
    else:
        if(arm[0][0] > arm[1][0]):
            point_tp = arm[1]
            point_elb = arm[0]
            point_bs = [arm[0][0]+10,arm[0][1]]

    return cord_angle(point_tp,point_elb,point_bs)
    
import cv2
import numpy as np
def get_pdf_box(line_ord):    
    points = np.array(line_ord, np.int32)

    min_x = np.min(points[:, 0])
    min_y = np.min(points[:, 1])

    for i in range(len(points)):
        points[i][0] -= min_x
        points[i][1] -= min_y

    canvas_height = int(np.max(points[:, 1]) + 1)

    points[:, 1] = canvas_height - points[:, 1]

    points = points.reshape((-1, 1, 2))

    min_rect = cv2.minAreaRect(points)
    rect_points = cv2.boxPoints(min_rect)
    rect_points = np.int32(rect_points)
    return rect_points


def rotate_points_2d(angle_deg, points):
  angle_rad = np.radians(angle_deg)
  rotation_matrix = np.array([
      [np.cos(angle_rad), -np.sin(angle_rad)],
      [np.sin(angle_rad), np.cos(angle_rad)]
  ])
  rotated_points = []
  for point in points:
    point = np.array(point)
    rotated_point = rotation_matrix.dot(point)
    rotated_points.append(rotated_point.tolist())
  return rotated_points


def resize_points_to_canvas(points, canvas_size):
  # Calculate bounding box of the points
  min_x = min(point[0] for point in points)
  max_x = max(point[0] for point in points)
  min_y = min(point[1] for point in points)
  max_y = max(point[1] for point in points)
  width = max_x - min_x
  height = max_y - min_y

  # Calculate scaling factors
  scale_x = canvas_size[0] / width
  scale_y = canvas_size[1] / height
  scale = min(scale_x, scale_y)  # Choose the smaller scale to fit within canvas

  # Calculate offset to center the points
  offset_x = (canvas_size[0] - width * scale) / 2
  offset_y = (canvas_size[1] - height * scale) / 2

  # Resize and reposition the points
  resized_points = []
  for point in points:
    new_x = (point[0] - min_x) * scale + offset_x
    new_y = (point[1] - min_y) * scale + offset_y
    resized_points.append([new_x, new_y])

  return resized_points,float(scale)