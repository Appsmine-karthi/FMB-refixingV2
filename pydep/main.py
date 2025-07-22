import fitz
import cv2
import numpy as np
from svgpathtools import parse_path
from cairosvg import svg2png
import requests
import json


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

def ExtractLandLines(drawings):
    line3 = []
    line1 = []
    line1_ = []
    for drawing in drawings:
        if(drawing["width"] == 3.0):
            temp = drawing["items"]
            line3.append([[temp[0][1][0],temp[0][1][1]], [temp[0][2][0],temp[0][2][1]]])
        if(drawing["width"] == 1.0):
            temp = drawing["items"]
            if(drawing["dashes"] == "[ 30 10 1 3 1 3 1 10 ] 1"):             
                line1_.append([[temp[0][1][0],temp[0][1][1]], [temp[0][2][0],temp[0][2][1]]])
            else:
                line1.append([[temp[0][1][0],temp[0][1][1]], [temp[0][2][0],temp[0][2][1]]])
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
            for j in range(i,i+4):
                try:
                    seg_ = path[j]
                except:
                    break
                if(seg_[0] == 'l'):
                    count.append(seg_)
            if(len(count) == 4):
                if(CheckDot(count)):
                    return True
            count = []
    return False

def ExtractTextD(drawings):
    r = []
    b = []
    for drawing in drawings:
        if(drawing["fill"] == (1.0, 0.0, 0.0)):
            r.append(drawing)
        elif(drawing["fill"] == (0.0, 0.0, 1.0)):
            if(not PathHasDot(drawing["items"])):
                b.append(drawing)
    return {"r":r,"b":b}

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
    return padded_img

def ExtractPdf(path):
    page = fitz.open(path)[0]
    drawings = page.get_drawings()
    page_rect = page.rect
    canvas_width = int(page_rect.width)
    canvas_height = int(page_rect.height)

    rtn = ExtractLandLines(drawings)
    textD = ExtractTextD(drawings)
    rtn["r"] = []
    for i in textD["r"]:
        img = MakeSvgImage(SvgToD(i["items"]))
        _, img_encoded = cv2.imencode('.png', img)
        img_bytes = img_encoded.tobytes()
        files = {'image': ('image.png', img_bytes, 'image/png')}
        response = requests.post('http://localhost:5000/ocr', files=files)
        bbox = i["rect"]
        rtn["r"].append({"text":response.json()['results'][0]['text'],"bbox": [bbox[0],bbox[1],bbox[2],bbox[3]]})
    rtn["b"] = []
    for i in textD["b"]:
        img = MakeSvgImage(SvgToD(i["items"]))
        _, img_encoded = cv2.imencode('.png', img)
        img_bytes = img_encoded.tobytes()
        files = {'image': ('image.png', img_bytes, 'image/png')}
        response = requests.post('http://localhost:5000/ocr', files=files)
        bbox = i["rect"]
        rtn["b"].append({"text":response.json()['results'][0]['text'],"bbox": [bbox[0],bbox[1],bbox[2],bbox[3]]})
    return json.dumps(rtn)


if __name__ == "__main__":
    print(ExtractPdf("source.pdf"))


def test(h):
    return str(h) + " test"