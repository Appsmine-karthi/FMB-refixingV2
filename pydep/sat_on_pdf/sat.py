URL = "https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z=18"
# URL = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/gwc/service/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=naturalcolor&STYLE=default&TILEMATRIXSET=EPSG:4326&TILEMATRIX=18&TILEROW={x}&TILECOL={y}&FORMAT=image/png"

import cv2
import requests
import numpy as np
import sat_on_pdf.funcs as func

width, height = round(575.27), round(721.89)

# pnt_wrld = {
#     "a":{
#         "lat": 11.423191800588633,
#         "lon": 78.00059913756809,
#     },
#     "b":{
#         "lat": 11.424515881038499,
#         "lon": 78.0012609398117,
#     }
# }

# pnt_pdf = {
#     "a":{
#         "x": -20.0+40-10,
#         "y": 303.1457237184471-10,
#     },
#     "b":{
#         "x": 90.89540336872793+40-10,
#         "y": 534.0605382341566-10
#     }
# }

def get_dis_of_img(p1,p2):
    ttl_tls = p2['tx'] - p1['tx']-1
    x = (256-p1['pix_cord_X']+256*ttl_tls+p2['pix_cord_X'])

    ttl_tls = p2['ty'] - p1['ty']-1
    y = (256-p1['pix_cord_Y']+256*ttl_tls+p2['pix_cord_Y'])

    return func.distance(p1['tx'],p1['ty'],p1['tx']+x,p1['ty']+y)

def place_image_on_another(img1, img2, x, y):
    # Get the dimensions of img2
    print("img1")
    h, w = img2.shape[:2]
    
    # Calculate the region of img1 where img2 should be placed
    start_x = max(x, 0)
    start_y = max(y, 0)
    end_x = min(x + w, img1.shape[1])
    end_y = min(y + h, img1.shape[0])

    # Calculate the region of img2 that will be placed on img1
    start_x_img2 = max(-x, 0)
    start_y_img2 = max(-y, 0)
    end_x_img2 = min(w, img1.shape[1] - x)
    end_y_img2 = min(h, img1.shape[0] - y)

    # Place the valid region of img2 onto img1
    img1[start_y:end_y, start_x:end_x] = img2[start_y_img2:end_y_img2, start_x_img2:end_x_img2]

    return img1

def get_sat_tile(x,y):
    response = requests.get(URL.format(x=x,y=y), stream=True)
    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
    tile = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return tile


def get_sat_img(pnt_wrld,pnt_pdf):
    image = np.zeros((height, width, 3), dtype=np.uint8)

    p1 = (func.get_tile_coordinates(pnt_wrld['a']['lat'],pnt_wrld['a']['lon'],18))
    p2 = (func.get_tile_coordinates(pnt_wrld['b']['lat'],pnt_wrld['b']['lon'],18))

    size_pdf = func.distance(int(pnt_pdf['a']['x']), int(pnt_pdf['a']['y']),int(pnt_pdf['b']['x']), int(pnt_pdf['b']['y']))
    size_tile = get_dis_of_img(p1,p2)

    scale = (size_pdf/size_tile)

    tile = get_sat_tile(p1['tx'],p1['ty'])

    image = place_image_on_another(image,tile,-p1['pix_cord_X']+int(pnt_pdf['a']['x']),height-int(pnt_pdf['a']['y'])-p1['pix_cord_Y'])
    cv2.circle(image, (int(pnt_pdf['a']['x']), height-int(pnt_pdf['a']['y'])), 5, (0,0,0), 3)

    top_left = func.relative_cord(-int(pnt_pdf['a']['x'])+p1['pix_cord_X'],-(height-int(pnt_pdf['a']['y']))+p1['pix_cord_Y'])
    bottom_right = func.relative_cord(width-int(pnt_pdf['a']['x'])+p1['pix_cord_X'],height-(height-int(pnt_pdf['a']['y'])-p1['pix_cord_Y']))

    print(top_left,bottom_right)

    ttl_tile_img = []

    img_x = (bottom_right[2]-top_left[2]+1)*256
    img_y = (bottom_right[3]-top_left[3]+1)*256
    img = np.zeros((img_y, img_x, 3), dtype=np.uint8)

    x_inc = 0
    y_inc = 0
    for y in range(top_left[3]+p1['ty'],bottom_right[3]+1+p1['ty']):
        for x in range(top_left[2]+p1['tx'],bottom_right[2]+1+p1['tx']):
            response = requests.get(URL.format(x=x,y=y), stream=True)
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            temp = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            print(x_inc,y_inc)
            place_image_on_another(img,temp,x_inc,y_inc)
            x_inc += 256
        y_inc += 256
        x_inc=0
    del x_inc
    del y_inc

    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

    x_ = round((top_left[2]*-256 + p1['pix_cord_X'])*scale)
    y_ = round((top_left[3]*-256 + p1['pix_cord_Y'])*scale)

    temp = np.zeros((height, width, 3), dtype=np.uint8)
    place_image_on_another(temp,img,-(x_-int(pnt_pdf['a']['x'])),-(y_-(height-int(pnt_pdf['a']['y']))))

    # cv2.imwrite("final.png",temp)
    return temp

# get_sat_img(pnt_wrld,pnt_pdf)