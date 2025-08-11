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
import dotenv
import os
import logging
import utm
from shapely.geometry import Point, Polygon, LineString
from collections import defaultdict
from typing import List
dotenv.load_dotenv()

inputsDir = os.getenv('INPUT_TEMP')
S3Domain = os.getenv('S3_DOMAIN')
S3PdfDir = os.getenv('S3_PDF_DIR')

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_REGION      = os.getenv('AWS_REGION')
BUCKET_NAME    = os.getenv('AWS_S3_BUCKET')


ocr_url = os.getenv('OCR_SERVER')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def SvgToD(geometry_data):
    # logger.info('Called SvgToD')
    try:
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
    except Exception as e:
        logger.error(f'Error in SvgToD: {e}')
        raise

def DownloadFile(url,LocalFileName):
    logger.info('Called DownloadFile')
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to download file from {url}: {e}')
        raise RuntimeError(f"Failed to download file from {url}: {e}")
    with open(LocalFileName, "wb") as f:
        f.write(response.content)

def ExtractLandLines(drawings, canvas_height):
    logger.info('Called ExtractLandLines')
    try:
        line3 = []
        line1 = []
        line1_ = []
        for drawing in drawings:
            temp = drawing["items"]
            if(drawing.get("color","") != (0.0, 0.0, 0.0)):
                continue
            if(drawing["width"] == 3.0 or drawing["width"] == 2.0):
                crd = [[temp[0][1][0],canvas_height - temp[0][1][1]], [temp[0][2][0],canvas_height - temp[0][2][1]]]
                line3.append(crd)
            if(drawing["width"] == 1.0):
                crd = [[temp[0][1][0],canvas_height - temp[0][1][1]], [temp[0][2][0],canvas_height - temp[0][2][1]]]
                if(drawing["dashes"] == "[ 30 10 1 3 1 3 1 10 ] 1"):
                    line1_.append(crd)
                else:
                    line1.append(crd)

        # to_remove = [
        #     [[2382.0, 0.0], [2382.0, 3369.0]],
        #     [[14.0, 14.0], [2369.0, 14.0]],
        #     [[2369.0, 14.0], [2369.0, 3356.0]],
        #     [[2369.0, 3356.0], [14.0, 3356.0]],
        #     [[14.0, 3356.0], [14.0, 14.0]],
        #     [[28.0, 3342.0], [28.0, 28.0]],
        #     [[28.0, 28.0], [2355.0, 28.0]],
        #     [[2355.0, 28.0], [2355.0, 3342.0]],
        #     [[2355.0, 3342.0], [28.0, 3342.0]]
        # ]

        # for line in to_remove:
        #     if line in line1:
        #         line1.remove(line)
        #     if line in line3:
        #         line3.remove(line)

        return {"line3":line3,"line1":line1,"line1_":line1_}
    except Exception as e:
        logger.error(f'Error in ExtractLandLines: {e}')
        raise

def CheckDot(count):
    # logger.info('Called CheckDot')
    try:
        if(count[0][1] == count[3][2]):
            return True
        return False
    except Exception as e:
        logger.error(f'Error in CheckDot: {e}')
        raise

def PathHasDot(path):
    # logger.info('Called PathHasDot')
    try:
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
    except Exception as e:
        logger.error(f'Error in PathHasDot: {e}')
        raise

def ExtractTextD(drawings, canvas_height):
    logger.info('Called ExtractTextD')
    try:
        r = []
        b = []
        for drawing in drawings:
            if(drawing["fill"] == (1.0, 0.0, 0.0)):
                r.append(drawing)
            elif(drawing["fill"] == (0.0, 0.0, 1.0)):
                if(not PathHasDot(drawing["items"])):
                    b.append(drawing)
        return {"r":r,"b":b}
    except Exception as e:
        logger.error(f'Error in ExtractTextD: {e}')
        raise

def ExtractScale(drawings):
    logger.info('Called ExtractScale')
    try:
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
    except Exception as e:
        logger.error(f'Error in ExtractScale: {e}')
        raise

def remove_floating_lines(lines: List[List[List[float]]]) -> List[List[List[float]]]:
    logger.info('Called remove_floating_lines')
    try:
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
    except Exception as e:
        logger.error(f'Error in remove_floating_lines: {e}')
        raise

def lines_to_ring(lines):
    logger.info('Called lines_to_ring')
    try:
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
    except Exception as e:
        logger.error(f'Error in lines_to_ring: {e}')
        raise

def MakeSvgImage(d):
    global bInd
    # logger.info('Called MakeSvgImage')
    try:
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
    except Exception as e:
        logger.error(f'Error in MakeSvgImage: {e}')
        raise

kl=0
def ExtractPdf(PdfName):
    global kl
    logger.info('Called ExtractPdf')
    try:
        DownloadFile(S3Domain+ "/fmb_refixing/" + S3PdfDir + PdfName, inputsDir + PdfName)
        page = fitz.open(inputsDir + PdfName)[0]
        drawings = page.get_drawings()
        page_rect = page.rect
        canvas_width = int(page_rect.width)
        canvas_height = int(page_rect.height)

        os.remove(inputsDir + PdfName)

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
            except Exception as e:
                logger.error(f'Error in ExtractPdf OCR r: {e}')
                continue

        rtn["b"] = []
        outer_polygon = remove_floating_lines(rtn["line3"])
        outer_polygon = lines_to_ring(outer_polygon)
        polygon = Polygon(outer_polygon)


        for i in textD["b"]:
            img, height = MakeSvgImage(SvgToD(i["items"]))
            kl += 1
            if height > 30:
                continue
            if not polygon.contains(Point(i["rect"][0], i["rect"][1])):
                continue
            if not polygon.contains(Point(i["rect"][2], i["rect"][3])):
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
            bbox = i["rect"]
            rtn["b"].append({"text": text, "bbox": [bbox[0], canvas_height - bbox[1], bbox[2], canvas_height - bbox[3]]})
            # print(rtn["line1"])
        return json.dumps(rtn)
    except Exception as e:
        logger.error(f'Error in ExtractPdf: {e}')
        raise

def getSubdiv(crd):
    logger.info('Called getSubdiv')
    try:
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
    except Exception as e:
        logger.error(f'Error in getSubdiv: {e}')
        raise

seed_point_offset = [0,0]
def get_div_cords(res,seed):
      logger.info('Called get_div_cords')
      try:
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
      except Exception as e:
          logger.error(f'Error in get_div_cords: {e}')
          raise

def calculate_distance(x1, y1, x2, y2):
    logger.info('Called calculate_distance')
    try:
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance
    except Exception as e:
        logger.error(f'Error in calculate_distance: {e}')
        raise

def calculate_area(points):
    # logger.info('Called calculate_area')
    try:
        n = len(points)
        area = 0
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            area += x1 * y2 - y1 * x2
        return abs(area) / 2
    except Exception as e:
        logger.error(f'Error in calculate_area: {e}')
        raise

def updateArea(data):
    logger.info('Called updateArea')
    try:
        for key, value in data['subdivision_list'].items():
            cycle_points = [data['coordinates'][point][0] for point in value[1]]
            data['subdivision_list'][key][2] = calculate_area(cycle_points)
    except Exception as e:
        logger.error(f'Error in updateArea: {e}')
        raise

def circle_line_intersection(x1, y1, r, x2, y2, x3, y3):
    logger.info('Called circle_line_intersection')
    try:
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
    except Exception as e:
        logger.error(f'Error in circle_line_intersection: {e}')
        raise

def updatelines(data, id, coordinate):
    logger.info('Called updatelines')
    try:
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
    except Exception as e:
        logger.error(f'Error in updatelines: {e}')
        raise

def build_adjacency_list(edges):
    logger.info('Called build_adjacency_list')
    try:
        graph = {}
        for u, v in edges:
            if u not in graph:
                graph[u] = []
            if v not in graph:
                graph[v] = []
            graph[u].append(v)
            graph[v].append(u)
        return graph
    except Exception as e:
        logger.error(f'Error in build_adjacency_list: {e}')
        raise

def find_longest_path(edges):
    logger.info('Called find_longest_path')
    try:
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
    except Exception as e:
        logger.error(f'Error in find_longest_path: {e}')
        raise

from func import *
import util
import flipMatch
def get_relative_points(obj,pix):#endpoints of pdf, endpoint of world
    logger.info('Called get_relative_points')
    try:
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

        normal = flipMatch.process(pdf_img,wld_img)
        # print("normal: ",normal)

        if(normal != -2):
            pdf_img = cv2.flip(pdf_img,normal)


        points = util.flip_points(points,normal==1 or normal==-1,normal==0 or normal==-1)

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

        return [[top_left_pdf,{'x':top_left_wld[0],'y':top_left_wld[1]}],[bottom_right_pdf,{'x':bottom_right_wld[0],'y':bottom_right_wld[1]}]]
    except Exception as e:
        logger.error(f'Error in get_relative_points: {e}')
        raise

import utm
def latlog_to_utm(lat, long):
    # logger.info('Called latlog_to_utm')
    try:
        easting, northing, zone_number, zone_letter = utm.from_latlon(lat, long)
        return {"x":easting,"y":northing}
    except Exception as e:
        logger.error(f'Error in latlog_to_utm: {e}')
        raise

def select_and_rotate_coords(data,coordinates,subdivision_list,rajaresponse):
    logger.info('Called select_and_rotate_coords')
    try:
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
    except Exception as e:
        logger.error(f'Error in select_and_rotate_coords: {e}')
        raise

def get_pdf_box_update(obj):
    logger.info('Called get_pdf_box_update')
    try:
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
    except Exception as e:
        logger.error(f'Error in get_pdf_box_update: {e}')
        raise

def shrink_or_expand_points(args):
    logger.info('Called shrink_or_expand_points')
    try:
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
    except Exception as e:
        logger.error(f'Error in shrink_or_expand_points: {e}')
        raise

def custom_sort_key(item):
    # logger.info('Called custom_sort_key')
    try:
        key = item
        if key.isdigit():
            return (1, int(key))
        else:
            return (0, key)
    except Exception as e:
        logger.error(f'Error in custom_sort_key: {e}')
        raise
def rotate(args,raja):
    logger.info('Called rotate')
    try:
        args = json.loads(args)
        coordinates = args["coordinates"]
        scale = args["Scale"]
        raja = json.loads(raja)

        args = select_and_rotate_coords(args,args["coordinates"],args["subdivision_list"],raja)
        args["Areass"] = []
        args["Scale"] = "1:"+str(scale)

        args["srt_coordinetes"] = sorted(list(coordinates.keys()), key=custom_sort_key)

        return json.dumps(args)
    except Exception as e:
        logger.error(f'Error in rotate: {e}')
        raise

def getPDF(req):
    logger.info('Called getPDF')
    try:
        req = json.loads(req)

        id = req['id']
        data = req['data']

        res = generatepdf(data,id)
        return res
    except Exception as e:
        logger.error(f'Error in getPDF: {e}')
        raise

from rotateCords import update_lines_with_new_slope_and_length
def getRotatedCoords(content):
    logger.info('Called getRotatedCoords')
    try:
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
    except Exception as e:
        logger.error(f'Error in getRotatedCoords: {e}')
        raise

def updateData(content):
    logger.info('Called updateData')
    try:
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
    except Exception as e:
        logger.error(f'Error in updateData: {e}')
        raise

def SelectAndRotateCoords(content):
    logger.info('Called SelectAndRotateCoords')
    try:
        content = json.loads(content)
        coordinates = content['coordinates']
        subdivision_list = content['subdivision_list']
        data = content['data']
        rajaresponse = content['rajaresponse']
        return json.dumps(select_and_rotate_coords(data, coordinates, subdivision_list, rajaresponse))
    except Exception as e:
        logger.error(f'Error in SelectAndRotateCoords: {e}')
        raise

from findSubDivWalls import CreateSubDivWalls, get_subdivision_edges
from pyproj import Proj, Transformer
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
def get_utm_coordinates(crd):
    logger.info('Called get_utm_coordinates')
    try:
        return transformer.transform(crd[0], crd[1])
    except Exception as e:
        logger.error(f'Error in get_utm_coordinates: {e}')
        raise
def updateFromKml(content):
    logger.info('Called updateFromKml')
    try:
        # with open("data.json", "w") as f:
        #     f.write(content)
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
            print(i)
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
    except Exception as e:
        logger.error(f'Error in updateFromKml: {e}')
        raise

from m import DrawReference_

def DrawReference(data):
    DrawReference_(data)
    return "done"

if __name__ == "__main__":
    f = ExtractPdf("/home/ubuntu/mypropertyqr-landsurvey/inputs/NAMAKKALKumarapalayamKokkarayanpettai88.pdf")
