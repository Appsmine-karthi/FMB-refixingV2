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

