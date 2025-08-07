import fitz
import cv2
import numpy as np
from svgpathtools import parse_path
from cairosvg import svg2png
import requests
import json
import math
import customFloodFill
from collections import Counter
from pdfGenerator import generatepdf

ocr_url = "http://localhost:6001/ocr"

def SvgToD(geometry_data):
    if not geometry_data:
        return ""

    path_commands = []
    subpath_start_point = None
    previous_end_point = None

    for segment in geometry_data:
        seg_type = segment[0]
        start_point = segment[1]
        end_point = segment[-1]

        if not previous_end_point or start_point != previous_end_point:
            path_commands.append(f"M {start_point.x} {start_point.y}")
            subpath_start_point = start_point

        if end_point == subpath_start_point:
            path_commands.append("Z")
        else:
            if seg_type == 'l':
                path_commands.append(f"L {end_point.x} {end_point.y}")
            elif seg_type == 'c':
                control1 = segment[2]
                control2 = segment[3]
                path_commands.append(
                    f"C {control1.x} {control1.y} {control2.x} {control2.y} {end_point.x} {end_point.y}"
                )
        
        previous_end_point = end_point

    return " ".join(path_commands)

def ExtractLandLines(drawings, canvas_height):
    line3 = []
    line1 = []
    line1_ = []
    for drawing in drawings:
        temp = drawing["items"]
        if(drawing.get("color","") == (0.0, 0.0, 1.0)):
            continue
        if(drawing["width"] == 3.0 or drawing["width"] == 2.0):
            crd = [[temp[0][1][0],canvas_height - temp[0][1][1]], [temp[0][2][0],canvas_height - temp[0][2][1]]]
            line3.append(crd)
        if(drawing["width"] == 1.0):
            crd = [[temp[0][1][0],canvas_height - temp[0][1][1]], [temp[0][2][0],canvas_height - temp[0][2][1]]]
            if(drawing["dashes"] == "[ 30 10 1 3 1 3 1 10 ] 1"):
                line1_.append(crd)
            else:
                if(1 not in crd[0] and 1 not in crd[1]):
                    line1.append(crd)


    to_remove_line1 = [
        [[2382.0, 0.0], [2382.0, 3369.0]]
    ]
    for line in to_remove_line1:
        if line in line1:
            line1.remove(line)

    to_remove_line3 = [
        [[14.0, 14.0], [2369.0, 14.0]],
        [[2369.0, 14.0], [2369.0, 3356.0]],
        [[2369.0, 3356.0], [14.0, 3356.0]],
        [[14.0, 3356.0], [14.0, 14.0]]
    ]
    for line in to_remove_line3:
        if line in line3:
            line3.remove(line)

    return {"line3":line3,"line1":line1,"line1_":line1_}

def CheckDot(count):
    if(count[0][1] == count[3][2]):
        return True
    return False

def PathHasDot(path):
    count = []
    for i in range(len(path)):
        seg = path[i]
        if seg[0] == 'l':
            for j in range(i, i + 4):
                try:
                    seg_ = path[j]
                except:
                    break
                if seg_[0] == 'l':
                    count.append(seg_)
            if len(count) == 4:
                if CheckDot(count):
                    return True
            count = []
    return False

def ExtractTextD(drawings, canvas_height):
    r = []
    b = []
    for drawing in drawings:
        if(drawing["fill"] == (1.0, 0.0, 0.0)):
            r.append(drawing)
        elif(drawing["fill"] == (0.0, 0.0, 1.0)):
            if(not PathHasDot(drawing["items"])):
                b.append(drawing)
    return {"r":r,"b":b}

def ExtractScale(drawings):
    ind = 0
    svg = ""
    path_data = SvgToD(drawings[len(drawings)-1]["items"])
    path_data = "M" + "M".join(path_data.split('M')[13:])
    img,height = MakeSvgImage(path_data)
    _, img_encoded = cv2.imencode('.png', img)
    img_bytes = img_encoded.tobytes()
    files = {'image': ('image.png', img_bytes, 'image/png')}
    response = requests.post(ocr_url, files=files)
    return response.json()['results'][0]['text']

from shapely.geometry import Point, Polygon, LineString
from collections import defaultdict
from typing import List
def remove_floating_lines(lines: List[List[List[float]]]) -> List[List[List[float]]]:
    class Point:
        def __init__(self, x: float, y: float):
            self.x = x
            self.y = y

        def __eq__(self, other):
            return isinstance(other, Point) and self.x == other.x and self.y == other.y

        def __hash__(self):
            return hash((round(self.x, 6), round(self.y, 6)))  # rounding for floating-point stability

    point_count = defaultdict(int)

    for line in lines:
        a = Point(line[0][0], line[0][1])
        b = Point(line[1][0], line[1][1])
        point_count[a] += 1
        point_count[b] += 1

    result = []
    for line in lines:
        a = Point((line[0][0]), line[0][1])
        b = Point(line[1][0], line[1][1])
        if point_count[a] > 1 and point_count[b] > 1:
            result.append(line)

    return result

def lines_to_ring(lines):
    # Flatten lines to get all points
    edges = {(tuple(p1), tuple(p2)) for p1, p2 in lines}
    
    # Build connectivity map
    from collections import defaultdict
    connections = defaultdict(list)
    for p1, p2 in edges:
        connections[p1].append(p2)
        connections[p2].append(p1)

    # Start at any point
    start = next(iter(connections))
    ring = [start]
    visited = set([start])

    current = start
    while True:
        neighbors = connections[current]
        for neighbor in neighbors:
            if neighbor not in visited:
                ring.append(neighbor)
                visited.add(neighbor)
                current = neighbor
                break
        else:
            break

    return ring
def MakeSvgImage(d):
    # Parse the path
    path = parse_path(d)
    xmin, xmax, ymin, ymax = path.bbox()
    width = xmax - xmin
    height = ymax - ymin

    # Desired canvas size
    canvas_size = 100

    # Calculate scaling and translation to center the path
    scale = min(canvas_size / width, canvas_size / height)
    tx = (canvas_size - width * scale) / 2 - xmin * scale
    ty = (canvas_size - height * scale) / 2 - ymin * scale

    svg_data = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_size}" height="{canvas_size}" viewBox="0 0 {canvas_size} {canvas_size}">
    <rect width="100%" height="100%" fill="white"/>
    <g transform="translate({tx},{ty}) scale({scale})">
        <path d="{d}" fill="black"/>
    </g>
    </svg>'''

    png_data = svg2png(bytestring=svg_data.encode('utf-8'))
    nparr = np.frombuffer(png_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # Add padding of 10 pixels on each side
    padding = 30
    padded_img = cv2.copyMakeBorder(img, 
                                   padding, padding, padding, padding,
                                   cv2.BORDER_CONSTANT,
                                   value=[255,255,255]) # White padding
    # Resize the padded image to 100x100
    padded_img = cv2.resize(padded_img, (100, 100))
    return padded_img,height

def ExtractPdf(path):
    page = fitz.open(path)[0]
    drawings = page.get_drawings()
    page_rect = page.rect
    canvas_width = int(page_rect.width)
    canvas_height = int(page_rect.height)

    rtn = ExtractLandLines(drawings, canvas_height)
    rtn["Scale"] = int(ExtractScale(drawings))
    textD = ExtractTextD(drawings, canvas_height)
    rtn["r"] = []
    for i in textD["r"]:
        img,height = MakeSvgImage(SvgToD(i["items"]))
        _, img_encoded = cv2.imencode('.png', img)
        img_bytes = img_encoded.tobytes()
        files = {'image': ('image.png', img_bytes, 'image/png')}
        response = requests.post(ocr_url, files=files)
        bbox = i["rect"]
        try:    
            rtn["r"].append({"text":response.json()['results'][0]['text'],"bbox": [bbox[0],canvas_height - bbox[1],bbox[2],canvas_height - bbox[3]]})
        except:
            continue

    rtn["b"] = []
    outer_polygon = remove_floating_lines(rtn["line3"])
    outer_polygon = lines_to_ring(outer_polygon)
    polygon = Polygon(outer_polygon)
    for i in textD["b"]:
        img, height = MakeSvgImage(SvgToD(i["items"]))
        if height > 8:
            # print("height")
            continue
        if not polygon.contains(Point(i["rect"][0], i["rect"][1])):
            # print("pol")
            continue
        if not polygon.contains(Point(i["rect"][2], i["rect"][3])):
            # print("pol2")
            continue
        _, img_encoded = cv2.imencode('.png', img)
        img_bytes = img_encoded.tobytes()
        files = {'image': ('image.png', img_bytes, 'image/png')}
        response = requests.post(ocr_url, files=files)
        ocr_results = response.json().get('results', [])
        if not ocr_results or not ocr_results[0].get('text', '').strip():
            text = ""
        else:
            text = ocr_results[0]['text']

        if text == "":
            continue
        # print(text)
        # cv2.imshow("img",img)
        # cv2.waitKey(0)
        bbox = i["rect"]
        rtn["b"].append({"text": text, "bbox": [bbox[0], canvas_height - bbox[1], bbox[2], canvas_height - bbox[3]]})
        # print(rtn["line1"])
    return json.dumps(rtn)

def getSubdiv(crd):

    crd = json.loads(crd)
    image = np.zeros((int(crd[4]+1), int(crd[3]+1), 3), dtype=np.uint8)
    ref_arr=[]

    lines = crd[1] + crd[2]
    cords = crd[0]
    ind = 0
    for i in lines:
        sp = (int(i[0][0]),int(i[0][1]))
        ep = (int(i[1][0]),int(i[1][1]))
        color = (ind,255,255)
        cv2.line(image, sp, ep, color, 1)
        ind += 1
        ref_arr.append(i)

    subdiv = {}
    for i in cords:
        line_ind = customFloodFill.process(image,int(cords[i]['X']),int(cords[i]['Y']))
        buc = Counter(map(str, line_ind))
        line_ind = [int(key) for key, count in buc.items() if count >= 10]

        subdiv[i] = []
        for e in line_ind:
            subdiv[i].append(ref_arr[e])

    return json.dumps(subdiv)

seed_point_offset = [0,0]
def get_div_cords(res,seed):
      image = np.zeros((int(res['y_max']+1), int(res['x_max']+1), 3), dtype=np.uint8)
      ind = 1
      ref_arr=[]

      for i in res['lines']:
          sp = (int(res['cords'][i[0]][0]),int(res['cords'][i[0]][1]))
          ep = (int(res['cords'][i[1]][0]),int(res['cords'][i[1]][1]))
          color = (ind,255,255)
          cv2.line(image, sp, ep, color, 1)
          ind += 1
          ref_arr.append(i)
      line_ind = customFloodFill.process(image,int(res['subdivision_list'][seed][0]+seed_point_offset[0]),int(res['subdivision_list'][seed][1]+seed_point_offset[1]))

      buc = Counter(map(str, line_ind))
      line_ind = [int(key) for key, count in buc.items() if count >= 5]

      i=0
      for e in line_ind:
            line_ind[i] = ref_arr[e-1]
            i += 1

      return line_ind

def calculate_distance(x1, y1, x2, y2):
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance

def calculate_area(points):
        n = len(points)
        area = 0
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            area += x1 * y2 - y1 * x2
        return abs(area) / 2

def updateArea(data):
    for key, value in data['subdivision_list'].items():
        cycle_points = [data['coordinates'][point][0] for point in value[1]]
        data['subdivision_list'][key][2] = calculate_area(cycle_points)

def circle_line_intersection(x1, y1, r, x2, y2, x3, y3):

    # Vector from point 2 to point 3
    dx = x3 - x2
    dy = y3 - y2

    # Vector from circle center to point 2
    fx = x2 - x1
    fy = y2 - y1

    # Quadratic equation coefficients
    a = dx**2 + dy**2
    b = 2 * (fx * dx + fy * dy)
    c = fx**2 + fy**2 - r**2

    # Compute the discriminant
    discriminant = b**2 - 4 * a * c

    if discriminant < 0:
        return [False]  # No intersection

    # Compute t values for line equation
    t1 = (-b - math.sqrt(discriminant)) / (2 * a)
    t2 = (-b + math.sqrt(discriminant)) / (2 * a)

    # Check if intersection points lie on the segment (0 ≤ t ≤ 1)
    if 0 <= t1 <= 1 or 0 <= t2 <= 1:

        intersection_x1 = x2 + t1 * dx
        intersection_y1 = y2 + t1 * dy
        intersection_x2 = x2 + t2 * dx
        intersection_y2 = y2 + t2 * dy
        final_x = (intersection_x1 + intersection_x2) / 2
        final_y = (intersection_y1 + intersection_y2) / 2
        return [True,final_x,final_y]  # Intersection occurs

    return [False,"notreq"] 

def updatelines(data, id, coordinate):
    lines = data['lines']
    new_lines = []
    j = 0
    for i in lines:
        lcoords = i['coordinates']
        if i['dashes'] != "[ 30 10 1 3 1 3 1 10 ] 1" and id != lcoords[0] and id != lcoords[1]:
            x1,y1 = coordinate[0], coordinate[1]
            x2,y2 = data['coordinates'][lcoords[0]][0][0], data['coordinates'][lcoords[0]][0][1]
            x3,y3 = data['coordinates'][lcoords[1]][0][0], data['coordinates'][lcoords[1]][0][1]
            result = circle_line_intersection(x1, y1, 3, x2, y2, x3, y3)
            # print("result ")
            # print(result)
            if result[0] == True:
                x = result[1]
                y = result[2]
                data['coordinates'][id][0] = [x,y]
                lines[j]['coordinates'] = [lcoords[0],id]
                new_lines.append({'coordinates':[lcoords[1],id],'dashes':i['dashes'],'strokewidth':i['strokewidth'],'length':0})
                break
        j += 1
    lines.extend(new_lines)
    data['lines'] = lines
    return data

def build_adjacency_list(edges):
    graph = {}
    for u, v in edges:
        if u not in graph:
            graph[u] = []
        if v not in graph:
            graph[v] = []
        graph[u].append(v)
        graph[v].append(u)
    return graph

def find_longest_path(edges):
    graph = build_adjacency_list(edges)
    def dfs(node, visited):
        visited.add(node)
        max_path = []
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                path = dfs(neighbor, visited)
                if len(path) > len(max_path):
                    max_path = path
        visited.remove(node)
        return [node] + max_path

    longest_path = []
    for start_node in graph:
        visited = set()
        path = dfs(start_node, visited)
        if len(path) > len(longest_path):
            longest_path = path
    # print("Longest Path:", longest_path,edges)
    return longest_path

from func import *
import util
import flipMatch
def get_relative_points(obj,pix):#endpoints of pdf, endpoint of world

    bound_rect = pix['bound_rect']
    box,points,point_ind = get_pdf_box(obj)

    wld_an = compute_angle((bound_rect))
    pdf_an = compute_angle((box))


    to_back_an = pdf_an-wld_an
    # print("points: ",points)
    points = points.reshape(-1,2)
    # print("points: ",points)
    
    points = util.rotate_points_clockwise(points , -to_back_an)
    # print("points: ",points)
    points = util.offset_points_top(points)
    # print("points: ",points)


    pix_points = pix['polygon']['pix']
    pix_points = util.offset_points_top(pix_points)

    w,h = util.get_width_height(pix_points)
    points = util.transform_points_to_fit(points,w,h)

    pdf_img = util.draw_box_ref(box,points)
    wld_img = util.draw_box_ref(bound_rect,pix_points)

    # if len(pdf_img.shape) == 2:
    #     pdf_img = cv2.cvtColor(pdf_img, cv2.COLOR_GRAY2BGR)
    # if len(wld_img.shape) == 2:
    #     wld_img = cv2.cvtColor(wld_img, cv2.COLOR_GRAY2BGR)
    # h1, w1 = pdf_img.shape[:2]
    # h2, w2 = wld_img.shape[:2]
    # target_height = max(h1, h2)
    # if h1 != target_height:
    #     pdf_img = cv2.resize(pdf_img, (w1 * target_height // h1, target_height))
    # if h2 != target_height:
    #     wld_img = cv2.resize(wld_img, (w2 * target_height // h2, target_height))
    # combined_img = np.hstack((pdf_img, wld_img))
    # cv2.imwrite("pdf_wld_rotate.png", combined_img)

    # cv2.imwrite("pdf.png",pdf_img)
    # cv2.imwrite("wld.png",wld_img)

    normal = flipMatch.process(pdf_img,wld_img)
    # print("normal: ",normal)

    if(normal != -2):
        pdf_img = cv2.flip(pdf_img,normal)

    # if len(pdf_img.shape) == 2:
    #     pdf_img = cv2.cvtColor(pdf_img, cv2.COLOR_GRAY2BGR)
    # if len(wld_img.shape) == 2:
    #     wld_img = cv2.cvtColor(wld_img, cv2.COLOR_GRAY2BGR)
    # h1, w1 = pdf_img.shape[:2]
    # h2, w2 = wld_img.shape[:2]
    # target_height = max(h1, h2)
    # if h1 != target_height:
    #     pdf_img = cv2.resize(pdf_img, (w1 * target_height // h1, target_height))
    # if h2 != target_height:
    #     wld_img = cv2.resize(wld_img, (w2 * target_height // h2, target_height))
    # combined_img = np.hstack((pdf_img, wld_img))
    # cv2.imwrite("pdf_wld_rotate_flip.png", combined_img)

    points = util.flip_points(points,normal==1 or normal==-1,normal==0 or normal==-1)
    # cv2.imshow("new",util.draw_box_ref(box,points))
    # cv2.waitKey(0)

    bottom_right_pdf = util.find_bottom_right_point_pix(points)
    # print("points: ",points)
    # print("bottom_right_pdf: ",bottom_right_pdf)
    for i in range(len(point_ind)):
        vald = (bottom_right_pdf == points[i])
        if vald[0] and vald[1]:
            bottom_right_pdf = point_ind[i]

    top_left_pdf = util.find_top_left_point_pix(points)
    for i in range(len(point_ind)):
        vald = (top_left_pdf == points[i])
        if vald[0] and vald[1]:
            top_left_pdf = point_ind[i]


    top_left_wld = util.find_top_left_point_geo(pix['polygon']['geo'])
    bottom_right_wld = util.find_bottom_right_point_geo(pix['polygon']['geo'])
    # print(pix['polygon']['geo'])
    # print(bottom_left_wld)
    # print(top_right_wld)
    # print([[top_right_pdf,{'x':top_right_wld[0],'y':top_right_wld[1]}],[bottom_left_pdf,{'x':bottom_left_wld[0],'y':bottom_left_wld[1]}]])
    # print(top_left_pdf, top_left_wld)
    # print(bottom_right_pdf, bottom_right_wld)
    return [[top_left_pdf,{'x':top_left_wld[0],'y':top_left_wld[1]}],[bottom_right_pdf,{'x':bottom_right_wld[0],'y':bottom_right_wld[1]}]]

import utm
def latlog_to_utm(lat, long):
    easting, northing, zone_number, zone_letter = utm.from_latlon(lat, long)
    return {"x":easting,"y":northing}

def select_and_rotate_coords(data,coordinates,subdivision_list,rajaresponse):

    ret = get_relative_points(data,rajaresponse)

    new_coord1 = latlog_to_utm(ret[0][1]['x'], ret[0][1]['y'])
    new_coord2 = latlog_to_utm(ret[1][1]['x'], ret[1][1]['y'])

    selected_point1 = ret[0][0]
    selected_point2 = ret[1][0]
    old_coord1 = {'x':coordinates[selected_point1][0][0],'y':coordinates[selected_point1][0][1]}
    old_coord2 = {'x':coordinates[selected_point2][0][0],'y':coordinates[selected_point2][0][1]}
    # print("nre ",new_coord1,new_coord2,selected_point1,selected_point2,old_coord1,old_coord2)
    out = update_lines_with_new_slope_and_length(new_coord1,new_coord2,old_coord1,old_coord2,coordinates,selected_point1,selected_point2,subdivision_list)
    data['coordinates'] = out['new_coords']
    data['subdivision_list'] = out['subdivision_list']
    # print("new requestr ",out)
    return data

def get_pdf_box_update(obj):
    line_ord = {
          'lines':[],
          'cords':{},
          'x_max':0,
          'y_max':0
    }
    for i in obj['lines']:
        if i['dashes'] == "[ 9 0 ] 1":
                    line_ord['lines'].append(i['coordinates'])
    for i in line_ord['lines']:
          for e in i:
                r = obj['coordinates'][e][0]
                line_ord['cords'][e] = r

    for i in obj['subdivision_list']:
          val = obj['subdivision_list'][i]
          line_ord['cords']["sub_"+i] = val[0]
      

    points = np.array(list(line_ord['cords'].values()))
    min_x, min_y = np.min(points, axis=0)
    offset_coords = {key: [x - min_x, y - min_y] for key, (x, y) in line_ord['cords'].items()}
    line_ord['cords'] = offset_coords

    for i in line_ord['cords']:
            val = line_ord['cords'][i]
            if line_ord['x_max'] < val[0]:
                  line_ord['x_max'] = val[0]
            if line_ord['y_max'] < val[1]:
                  line_ord['y_max'] = val[1]
    
    line_ord['subdivision_list'] = {}
    temp = line_ord['cords'].copy()
    for i in temp:
          k = i.split('_')
          if k[0] == "sub":
            val = line_ord['cords'][i]
            line_ord['subdivision_list'][k[1]] = val
            del line_ord['cords'][i]

      
    return(line_ord)

def shrink_or_expand_points(args):
    args = json.loads(args)
    points = args["coordinates"]
    subdivision = args["subdivision_list"]
    scale = args["Scale"]

    # print(subdivision)
    # return "args"

    # Calculate the centroid (center) of the points
    point_keys = list(points.keys())
    subdivision_keys = list(subdivision.keys())

    x1 = points[point_keys[0]][0][0]
    y1 = points[point_keys[0]][0][1]
    x2 = points[point_keys[1]][0][0]
    y2 = points[point_keys[1]][0][1]

    initialdist = calculate_distance(x1, y1, x2, y2)
    newdist = initialdist * 0.03535 * scale / 100
    percentage = (newdist - initialdist) / initialdist * 100
    # print("Percetage: ",percentage)

    n = len(point_keys)
    n1 = len(subdivision_keys)

    centroid_x = 0
    centroid_y = 0

    for key in point_keys:
        centroid_x += points[key][0][0]
        centroid_y += points[key][0][1]

    for key in subdivision_keys:
        centroid_x += subdivision[key][0][0]
        centroid_y += subdivision[key][0][1]

    centroid_x = centroid_x / (n + n1)
    centroid_y = centroid_y / (n + n1)

    # Calculate the new scaled points
    scaled_points = {}
    subdiv_points = {}

    for key, value in points.items():
        vector_x = value[0][0] - centroid_x
        vector_y = value[0][1] - centroid_y

        new_x = centroid_x + vector_x * (1 + percentage / 100)
        new_y = centroid_y + vector_y * (1 + percentage / 100)

        scaled_points[key] = [[new_x, new_y], value[1], value[2]]

    for key, value in subdivision.items():
        vector_x = value[0][0] - centroid_x
        vector_y = value[0][1] - centroid_y

        new_x = centroid_x + vector_x * (1 + percentage / 100)
        new_y = centroid_y + vector_y * (1 + percentage / 100)

        subdiv_points[key] = [[new_x, new_y], value[1], value[2]]

    args["coordinates"] = scaled_points
    args["subdivision_list"] = subdiv_points

    updateArea(args)

    # args = select_and_rotate_coords(args,args["coordinates"],args["subdivision_list"],raja)

    return json.dumps(args)

def custom_sort_key(item):
    key = item
    if key.isdigit():
        return (1, int(key))
    else:
        return (0, key)
def rotate(args,raja):
    args = json.loads(args)
    coordinates = args["coordinates"]
    scale = args["Scale"]
    raja = json.loads(raja)

    args = select_and_rotate_coords(args,args["coordinates"],args["subdivision_list"],raja)
    args["Areass"] = []
    args["Scale"] = "1:"+str(scale)

    args["srt_coordinetes"] = sorted(list(coordinates.keys()), key=custom_sort_key)

    return json.dumps(args)

def getPDF(req):
    req = json.loads(req)

    id = req['id']
    data = req['data']

    res = generatepdf(data,id)
    return res

from rotateCords import update_lines_with_new_slope_and_length
def getRotatedCoords(content):
    content = json.loads(content)
    new_coord1 = content['new_coord1']
    new_coord2 = content['new_coord2']
    old_coord1 = content['old_coord1']
    old_coord2 = content['old_coord2']
    coordinates = content['coordinates']
    selected_point1 = content['selected_point1']
    selected_point2 = content['selected_point2']
    subdivision_list = content['subdivision_list']
    out = update_lines_with_new_slope_and_length(new_coord1,new_coord2,old_coord1,old_coord2,coordinates,selected_point1,selected_point2,subdivision_list)
    return json.dumps(out)

def updateData(content):
    content = json.loads(content)
    # with open("data.json","w") as f:
    #     json.dump(content,f)
    data = content['data']
    event = content['event']
    if event == "coordinatedrag":
         id = content['id']
         coordinate = data['coordinates'][id][0]
        #  print("new cord ",coordinate)
         data = updatelines(data, id, coordinate)
    subdivisions = {}
    res = get_pdf_box_update(data)
    for key, value in data["subdivision_list"].items():
        coordinates, points, area = value
        # print("for ",key)
        path = find_longest_path(get_div_cords(res,key))
        cycle_points = [data['coordinates'][point][0] for point in path]
        area = calculate_area(cycle_points)
        print(area)
        subdivisions[key] = [coordinates,path,area]
    # print(subdivisions)
    data['subdivision_list'] = subdivisions

    return json.dumps(data)

def SelectAndRotateCoords(content):
    content = json.loads(content)
    coordinates = content['coordinates']
    subdivision_list = content['subdivision_list']
    data = content['data']
    rajaresponse = content['rajaresponse']
    return json.dumps(select_and_rotate_coords(data, coordinates, subdivision_list, rajaresponse))

from findSubDivWalls import CreateSubDivWalls, get_subdivision_edges
from pyproj import Proj, Transformer
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
def get_utm_coordinates(crd):
    return transformer.transform(crd[0], crd[1])
def updateFromKml(content):
    with open("data.json", "w") as f:
        f.write(content)
    content = json.loads(content)

    data = {
        "lines": [],
        "subdivision_list": {},
        "coordinates": {},
        "srt_coordinetes": [],
        "district": content.get("district", ""),
        "taluk": content.get("taluk", ""),
        "village": content.get("village", ""),
        "survey_no": content.get("survey_no", ""),
        "Scale": "1:1",
        "Note": "Manualy uploaded"
    }

    walls = [i["coordinates"] for i in content.get("Line1", [])]
    walls += [i["coordinates"] for i in content.get("Line2", [])]

    seeds, seedLabels = zip(*(
        (i["coordinates"], i["label"])
        for i in content.get("Text3", [])
        if '.' not in i["label"]
    )) if content.get("Text3") else ([], [])

    stoneIndex = {
        tuple(crd): i["label"]
        for i in content.get("Text2", [])
        for crd in [i["coordinates"]]
    }

    polygons = CreateSubDivWalls(walls)
    wall_segments = get_subdivision_edges(polygons, seeds)

    subDiv = {
        seedLabels[i]: [
            stoneIndex.get(tuple(j[0]), "")
            for j in wall_segments[i]
        ]
        for i in range(len(wall_segments))
    }

    for i in range(len(seedLabels)):
        seedT = seedLabels[i]
        wallT = wall_segments[i]
        seedCrd = get_utm_coordinates(seeds[i])
        data["subdivision_list"][seedT] = [seedCrd,subDiv[seedT],0]

    for key, value in stoneIndex.items():
        data["coordinates"][value] = [get_utm_coordinates(key),"main",["notmodified","notmodified"]]

    for i in content.get("Line3", []):
        a = stoneIndex.get(tuple(i["coordinates"][0]), "")
        b = stoneIndex.get(tuple(i["coordinates"][1]), "")

        a_ = data["coordinates"][a][0]
        b_ = data["coordinates"][b][0]

        distance = calculate_distance(a_[0],a_[1],b_[0],b_[1])
        data["lines"].append({"coordinates":[a,b], "dashes":"[ 30 10 1 3 1 3 1 10 ] 1","length":distance,"strokewidth":1})
    for i in content.get("Line1", []):
        a = stoneIndex.get(tuple(i["coordinates"][0]), "")
        b = stoneIndex.get(tuple(i["coordinates"][1]), "")

        a_ = data["coordinates"][a][0]
        b_ = data["coordinates"][b][0]

        distance = calculate_distance(a_[0],a_[1],b_[0],b_[1])
        data["lines"].append({"coordinates":[a,b], "dashes":"[ 9 0 ] 1","length":distance,"strokewidth":1})
    for i in content.get("Line2", []):
        a = stoneIndex.get(tuple(i["coordinates"][0]), "")
        b = stoneIndex.get(tuple(i["coordinates"][1]), "")

        a_ = data["coordinates"][a][0]
        b_ = data["coordinates"][b][0]

        distance = calculate_distance(a_[0],a_[1],b_[0],b_[1])
        data["lines"].append({"coordinates":[a,b], "dashes":"[ 9 0 ] 1","length":distance,"strokewidth":3})


    data["srt_coordinetes"] = sorted(list(data["coordinates"].keys()), key=custom_sort_key)

    updateArea(data)
    return json.dumps(data)

if __name__ == "__main__":
    f = ExtractPdf("/home/ubuntu/mypropertyqr-landsurvey/inputs/NAMAKKALKumarapalayamKokkarayanpettai88.pdf")
