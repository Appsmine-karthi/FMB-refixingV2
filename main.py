import fitz  # PyMuPDF
import cv2
import numpy as np
from xml.dom.minidom import Document
from svgpathtools import parse_path
from cairosvg import svg2png

page = fitz.open("source.pdf")[0]
drawings = page.get_drawings()
page_rect = page.rect
canvas_width = int(page_rect.width)
canvas_height = int(page_rect.height)

def SvgToImg(geometry_data):
    if not geometry_data:
        return ""

    path_commands = []
    subpath_start_point = None
    previous_end_point = None

    for segment in geometry_data:
        seg_type = segment[0]
        start_point = segment[1]
        end_point = segment[-1]

        # Start a new subpath with 'M' if it's the first segment
        # or if it's disconnected from the previous one.
        if not previous_end_point or start_point != previous_end_point:
            path_commands.append(f"M {start_point.x} {start_point.y}")
            subpath_start_point = start_point

        # Use 'Z' to close the path if a segment ends where the subpath started.
        # This is more efficient than drawing the last line segment.
        if end_point == subpath_start_point:
            path_commands.append("Z")
        else:
            # Add the appropriate command for the segment type.
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

def extract_land_boundary(stroke_width_threshold=3.0):
    elms = []
    for drawing in drawings:
        if(drawing["width"] == stroke_width_threshold):
            elms.append(drawing["items"])
    return elms

def extract_red():
    elms = []
    for drawing in drawings:
        if(drawing["fill"] == (1.0, 0.0, 0.0)):
            elms.append(drawing["items"])
    return elms

def draw_polygons_on_canvas(polygons, canvas_width, canvas_height, output_path):
    # Create a white canvas
    canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255
    
    # Color for drawing (black)
    color = (0, 0, 0)
    thickness = 2
    text_color = (255, 0, 0)  # Red color for measurements
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    text_thickness = 1
    
    for polygon_items in polygons:
        for item in polygon_items:
            item_type = item[0]
            
            if item_type == 'l':  # Line
                # Extract start and end points
                start_point = item[1]
                end_point = item[2]
                
                # Convert to integer coordinates
                pt1 = (int(start_point.x), int(start_point.y))
                pt2 = (int(end_point.x), int(end_point.y))
                
                # Calculate distance (measurement)
                distance = np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)
                
                # Calculate midpoint for text placement
                mid_x = (pt1[0] + pt2[0]) // 2
                mid_y = (pt1[1] + pt2[1]) // 2
                
                # Draw line
                cv2.line(canvas, pt1, pt2, color, thickness)
                
                # Add measurement text
                measurement_text = f"{distance:.1f}"
                
                # Calculate text size to center it properly
                text_size = cv2.getTextSize(measurement_text, font, font_scale, text_thickness)[0]
                text_x = mid_x - text_size[0] // 2
                text_y = mid_y + text_size[1] // 2
                
                # Add a small background rectangle for better text visibility
                padding = 3
                # cv2.rectangle(canvas, 
                #              (text_x - padding, text_y - text_size[1] - padding),
                #              (text_x + text_size[0] + padding, text_y + padding),
                #              (255, 255, 255), -1)
                
                # Draw the measurement text
                # cv2.putText(canvas, measurement_text, (text_x, text_y), 
                #            font, font_scale, text_color, text_thickness)

    cv2.imwrite(output_path, canvas)
    print(f"Graphics saved to {output_path}")
    return canvas

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
    <g transform="translate({tx},{ty}) scale({scale})">
        <path d="{d}" fill="black"/>
    </g>
    </svg>'''

    print(svg_data)
    svg2png(bytestring=svg_data.encode('utf-8'), write_to="img.png")

boundry = extract_land_boundary()
draw_polygons_on_canvas(boundry, canvas_width, canvas_height,"boundry.png")

red_text = extract_red()
draw_polygons_on_canvas(red_text, canvas_width, canvas_height,"red_text.png")

MakeSvgImage(SvgToImg(red_text[0]))