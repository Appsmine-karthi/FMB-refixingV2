import math
def euc(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def cord_angle(p1, p2, p3):

    # print("top: ",p1)
    # print("elb: ",p2)
    # print("bse: ",p3)

    print(p1)
    print()
    print(p2)
    print()
    print(p3)

    print(p1[0] - p2[0], p1[1] - p2[1])
    print(p3[0] - p2[0], p3[1] - p2[1])


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
    # print("test")
    # print(pts)
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
    
def arrange_chain(arr):
    chain = [arr[0]]
    remaining = arr[1:]

    for _ in range(len(arr) - 1):
        end = chain[-1][1]
        found = False
        for i, e in enumerate(remaining):
            if e[0] == end:
                chain.append(e)
                remaining.pop(i)
                found = True
                break
            elif e[1] == end:
                chain.append([e[1], e[0]])  # reverse the direction
                remaining.pop(i)
                found = True
                break
        if not found:
            break

    chn_car = [i[0] for i in chain]
    return chn_car

import cv2
import numpy as np
def get_pdf_box(obj):
    line_ord = []
    for i in obj['lines']:
        if i['strokewidth'] == "3":
            line_ord.append(i['coordinates'])

    # l = []
    # for i in line_ord:
    #     l.append([[int(obj['coordinates'][i[0]][0][0]),int(obj['coordinates'][i[0]][0][1])],[int(obj['coordinates'][i[1]][0][0]),int(obj['coordinates'][i[1]][0][1])]])

    point_ind = arrange_chain(line_ord)

    temp = []
    for i in point_ind:
        temp.append(obj['coordinates'][i][0])

    points = np.array(temp, np.int32)

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
    return rect_points,points,point_ind

import math
def update_lines_with_new_slope_and_length(new_coord1,new_coord2,old_coord1,old_coord2,coordinates,selected_point1,selected_point2,subdivision_list):
    x1, y1 = float(new_coord1['x']), float(new_coord1['y'])
    x3, y3 = float(new_coord2['x']), float(new_coord2['y'])
    x4, y4 = float(old_coord1['x']), float(old_coord1['y'])
    x5, y5 = float(old_coord2['x']), float(old_coord2['y'])
    new_coords = {}
    new_subdivision = {}

    def calculate_new_coord():
        for key, value in coordinates.items():
            if key != selected_point1 and key != selected_point2:
                x2, y2 = value[0]
                end_point_positive = calculate_new_position(x4, y4, x2, y2, x5, y5, x1, y1, x3, y3)
                new_x2 = round(end_point_positive['x'], 3)
                new_y2 = round(end_point_positive['y'], 3)
                new_coords[key] = [[new_x2, new_y2], value[1], value[2]]
            elif key == selected_point1:
                new_coords[selected_point1] = [[round(float(new_coord1['x']),3), round(float(new_coord1['y']),3)], value[1], value[2]]
            else:
                new_coords[selected_point2] = [[round(float(new_coord2['x']),3), round(float(new_coord2['y']),3)], value[1], value[2]]
        for key, value in subdivision_list.items():
            x2, y2 = value[0]
            end_point_positive = calculate_new_position(x4, y4, x2, y2, x5, y5, x1, y1, x3, y3)
            new_x2 = round(end_point_positive['x'], 3)
            new_y2 = round(end_point_positive['y'], 3)
            new_subdivision[key] = [[new_x2, new_y2], value[1], value[2]]

        return {'new_coords':new_coords,'subdivision_list':new_subdivision}

    return calculate_new_coord()

def calculate_new_position(ax, ay, bx, by, cx, cy, ax_new, ay_new, cx_new, cy_new):
    initial_angle = math.atan2(cy - ay, cx - ax)
    new_angle = math.atan2(cy_new - ay_new, cx_new - ax_new)
    rotation_angle = new_angle - initial_angle
    translation_vector = {'x': ax_new - ax, 'y': ay_new - ay}
    rotated_b = rotate_point(bx, by, ax, ay, rotation_angle)
    new_b = {
        'x': rotated_b['x'] + translation_vector['x'],
        'y': rotated_b['y'] + translation_vector['y']
    }
    return new_b

def rotate_point(px, py, ox, oy, angle):
    translated_px = px - ox
    translated_py = py - oy
    rotated_px = translated_px * math.cos(angle) - translated_py * math.sin(angle)
    rotated_py = translated_px * math.sin(angle) + translated_py * math.cos(angle)
    new_px = rotated_px + ox
    new_py = rotated_py + oy
    return {'x': new_px, 'y': new_py}

