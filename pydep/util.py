import numpy as np
import cv2
from scipy.signal import savgol_filter
from scipy.spatial.distance import directed_hausdorff


def draw_box_ref(arr,pol):
    # Define the points
    points = np.array(pol,int)

    # Identify the max and min points
    min_point = np.min(points, axis=0)
    max_point = np.max(points, axis=0)

    # Calculate the width and height (ensure they're positive)
    width = max_point[0] - min_point[0]
    height = max_point[1] - min_point[1]

    # Add some padding to ensure there is space around the points
    padding = 0
    canvas_width = width + padding * 2
    canvas_height = height + padding * 2

    # padding = 0
    # canvas_width = width
    # canvas_height = height

    # Create a white canvas with the new size
    canvas = np.ones((canvas_height, canvas_width, 3), dtype="uint8") * 255

    # Shift the points to fit into the positive area
    shifted_points = points - min_point + padding

    # Draw lines connecting the points
    for i in range(len(shifted_points) - 1):
        cv2.line(canvas, tuple(shifted_points[i]), tuple(shifted_points[i + 1]), (0, 0, 255), 2)
    cv2.line(canvas, tuple(shifted_points[0]), tuple(shifted_points[len(shifted_points) - 1]), (0, 0, 255), 2)

    #draw pol
    pol = pol - min_point +  padding
    cv2.polylines(canvas, [pol], isClosed=True, color=(0, 0, 255), thickness=3)

    # Display the image
    return canvas

def rotate_points_clockwise(points, angle_degrees):

    # Ensure points are the correct type for cv2.getRotationMatrix2D
    points = np.array(points, dtype=np.float32)

    # Calculate the center of the points
    center = np.mean(points, axis=0)

    # Create the rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D(center, angle_degrees, 1.0)  # 1.0 is the scale factor

    # Reshape points for matrix multiplication (N, 1, 2)
    reshaped_points = points.reshape(-1, 1, 2)

    # Apply the rotation
    rotated_points = cv2.transform(reshaped_points, rotation_matrix).reshape(-1, 2)

    return rotated_points


def offset_points_top(points):

    # Convert points to numpy array if not already
    points = np.array(points)
    
    # Get the min Y value (this is where the offset happens)
    min_y = np.min(points[:, 1])
    
    # Offset the points upwards by shifting all Y coordinates by -min_y
    offset_points = points - [0, min_y]
    offset_points = np.round(offset_points).astype(np.int32)
    # Calculate the bounding box of the offset polygon
    # x, y, w, h = cv2.boundingRect(offset_points)
    
    return offset_points


def transform_points_to_fit(points, width, height):

    try:
        points = np.array(points, dtype=np.float32)  # Ensure correct type
        min_x = np.min(points[:, 0])
        min_y = np.min(points[:, 1])
        max_x = np.max(points[:, 0])
        max_y = np.max(points[:, 1])

        original_width = max_x - min_x
        original_height = max_y - min_y

        if original_width == 0 or original_height == 0: #handle edge case
            return points

        x_scale = width / original_width
        y_scale = height / original_height

        # Scale the points
        scaled_points = points * np.array([x_scale, y_scale])

        # Calculate the offset to center the scaled points
        scaled_min_x = np.min(scaled_points[:, 0])
        scaled_min_y = np.min(scaled_points[:, 1])

        x_offset = (width - (np.max(scaled_points[:,0]) - scaled_min_x)) /2 - scaled_min_x if (np.max(scaled_points[:,0]) - scaled_min_x) < width else -scaled_min_x
        y_offset = (height - (np.max(scaled_points[:,1]) - scaled_min_y)) /2 - scaled_min_y if (np.max(scaled_points[:,1]) - scaled_min_y) < height else -scaled_min_y


        # Apply the offset
        transformed_points = scaled_points + np.array([x_offset, y_offset])

        transformed_points = np.round(transformed_points).astype(np.int32)

        return transformed_points
    except Exception as e:
        print(f"An error occurred: {e}")
        return points  # Return original points in case of error
    

def get_width_height(points):
    min_point = np.min(points, axis=0)
    max_point = np.max(points, axis=0)

    # Calculate the width and height (ensure they're positive)
    width = max_point[0] - min_point[0]
    height = max_point[1] - min_point[1]
    return width,height


def flip_points(points, flip_horizontal=False, flip_vertical=False):
    # Find the image width and height automatically
    image_width = np.max(points[:, 0])
    image_height = np.max(points[:, 1])

    flipped_points = points.copy()
    
    if flip_horizontal:
        flipped_points[:, 0] = image_width - points[:, 0]
    
    if flip_vertical:
        flipped_points[:, 1] = image_height - points[:, 1]
    
    return flipped_points

# def find_bottom_right_point_pix(points):
#     return max(points, key=lambda p: (p[1], p[0]))

# def find_top_left_point_pix(points):
#     return min(points, key=lambda p: (p[1], p[0]))

def find_top_left_point_geo(points): #lattitude, longitude
    return max(points, key=lambda p: (p[0], p[1]))

def find_bottom_right_point_geo(points): #lattitude, longitude
    return min(points, key=lambda p: (p[0], p[1]))

import math
def find_bottom_right_point_pix(points):
    # Get the bounding box of the polygon
    max_x = max(p[0] for p in points)
    max_y = max(p[1] for p in points)
    target = (max_x, max_y)

    # Compute distance to (maxX, maxY) for each point
    def distance(p):
        return math.hypot(p[0] - target[0], p[1] - target[1])

    # Return the point closest to the bottom-right corner of the frame
    return min(points, key=distance)

def find_top_left_point_pix(points):
    # Get the bounding box of the polygon
    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)
    target = (min_x, min_y)

    # Compute distance to (minX, minY) for each point
    def distance(p):
        return math.hypot(p[0] - target[0], p[1] - target[1])

    # Return the point closest to the top-left corner of the frame
    return min(points, key=distance)