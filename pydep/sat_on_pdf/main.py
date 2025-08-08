# from datas import data #source data
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import cv2
import pos
import sat
import math
import funcs as func

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from io import BytesIO
from PIL import Image
import numpy as np
from reportlab.lib.colors import Color

import os
from dotenv import load_dotenv
load_dotenv()
logo = os.getenv("LOGO")

def generatepdfpage1(data,file_name):
    keys = {}
    pnts = {}

    for i in data['duppoints']:
        keys[i['key']] = [i['latitude']*1,i['longitude']*1]

    for i in data['points']:
        pnts[i['key']]={"lat":i["latitude"],"lon":i["longitude"]}

    page_margin = 20
    dig_padding = 10
    top_marg = 100

    min_x=595.27
    min_y=841.89

    transform_mem = []
    for i in keys:
        transform_mem.append(keys[i])
    
    subdiv_trans_mem = []
    for i,e in data['subdivision_list'].items():
        subdiv_trans_mem.append(e[0])
    temp = transform_mem+subdiv_trans_mem
    temp,scale = pos.resize_points_to_canvas(temp,[595.27-2*page_margin, 841.89-(2*page_margin + top_marg)])
    transform_mem = temp[:len(transform_mem)]
    subdiv_trans_mem = temp[-len(subdiv_trans_mem):]

    for i in keys:
        k=transform_mem.pop(0)
        if min_x > k[0]-page_margin:
            min_x = k[0]-page_margin
        if min_y > k[1]+page_margin:
            min_y = k[1]+page_margin
        keys[i] = [k[0]-page_margin,k[1]+page_margin]

    #pdf
    pdf_canvas = canvas.Canvas(file_name)
    width, height = A4

    if min_x < page_margin:
        min_x = page_margin - min_x
    else:
        min_x = 0

    if min_y > height-page_margin:
        min_y = min_y - height-page_margin
    else:
        min_y = 0


    max_length=max(item["coordinates"] for item in data['lines'])
    pnt_wrld = {
        "a":pnts[max_length[0]],
        "b":pnts[max_length[1]]
    }
    pnt_pdf = {
        "a":{
            "x": keys[max_length[0]][0]+40-10,
            "y": keys[max_length[0]][1]-10,
        },
        "b":{
            "x": keys[max_length[1]][0]+40-10,
            "y": keys[max_length[1]][1]-10,
        }
    }


    #images
    image = sat.get_sat_img(pnt_wrld,pnt_pdf)
    image = cv2.addWeighted( image, 0.8, image, 0, 0)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    image_buffer = BytesIO()
    pil_image.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    pdf_canvas.drawImage(ImageReader(image_buffer), x=page_margin-dig_padding, y=page_margin-dig_padding,mask='auto')
    pdf_canvas.drawImage(logo, x=page_margin+10, y=height-85, width = 150*2, height= 35*2,mask='auto')


    #margin
    page_margin -= dig_padding
    pdf_canvas.setStrokeColorRGB(0, 0, 0)
    pdf_canvas.setLineWidth(1)

    pdf_canvas.line(page_margin,page_margin,width-(page_margin),page_margin)
    pdf_canvas.line(width-(page_margin),page_margin,width-page_margin,height-page_margin)
    pdf_canvas.line(width-page_margin,height-page_margin,page_margin,height-page_margin)
    pdf_canvas.line(page_margin,height-page_margin,page_margin,page_margin)

    pdf_canvas.line(page_margin,height-(page_margin + top_marg),width-(page_margin),height-(page_margin + top_marg))

    pdf_canvas.setFont("Helvetica-Bold", 11)

    for i in data['lines']:
        cord = i['coordinates']
        dashes_pattern = [int(val) for val in i["dashes"].replace("[", "").replace("]", "").split() if val.isdigit()][:2]
        stk = int(i["strokewidth"])
        pdf_canvas.setLineWidth(stk)
        pdf_canvas.setFillColor(Color(2/255, 125/255, 220/255)) 
        if stk == 3:
            pdf_canvas.setStrokeColorRGB(207/255, 255/255, 0/255)
        elif stk == 1:
           pdf_canvas.setStrokeColorRGB(149/255, 11/255, 220/255)
        
        if len(dashes_pattern) % 2 == 0:
            pdf_canvas.setDash(*dashes_pattern[:2])
        if dashes_pattern != [9, 0]:
            pdf_canvas.setStrokeColorRGB(0.5,0.5,0.5)

        x1=int(keys[i['coordinates'][1]][0]+min_x)
        y1=int(keys[i['coordinates'][1]][1]-min_y)
        x2=int(keys[i['coordinates'][0]][0]+min_x)
        y2=int(keys[i['coordinates'][0]][1]-min_y)

        x1_=(pnts[i['coordinates'][1]]['lat'])
        y1_=(pnts[i['coordinates'][1]]['lon'])
        x2_=(pnts[i['coordinates'][0]]['lat'])
        y2_=(pnts[i['coordinates'][0]]['lon'])
        pdf_canvas.line(x1,y1,x2,y2)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        text_x = (x1 + x2) / 2  # Middle of the line
        text_y = (y1 + y2) / 2 + 10  # Slightly above the line
        pdf_canvas.saveState()
        pdf_canvas.translate(text_x, text_y)
        pdf_canvas.rotate(angle)
        pdf_canvas.drawString(0, 0, f"{func.haversine(x1_,y1_,x2_,y2_)*1000:.1f}")
        pdf_canvas.restoreState()

    #write subdiv
    subdivs_lst_cntr = 0
    
    for i in data['subdivision_list']:
        subdiv_cord = subdiv_trans_mem[subdivs_lst_cntr]
        pdf_canvas.setFont("Helvetica-Bold", 13)
        pdf_canvas.setFillColor((79/255,190/255,23/255))
        pdf_canvas.drawString(x=subdiv_cord[0],y=subdiv_cord[1],text=i)
        pdf_canvas.setFont("Helvetica-Bold", 9)
        pdf_canvas.setFillColor((79/255,190/255,23/255))
        area = (data['subdivision_list'][i][2] * 10.7636) / 435.6 / 100
        tmp_st = f"{area:.2f}"
        pdf_canvas.drawString(x=subdiv_cord[0] - (len(tmp_st)*1),y=subdiv_cord[1]-10,text=tmp_st)
        subdivs_lst_cntr += 1

    pdf_canvas.setFillColor(Color(239/255, 88/255, 125/255)) 
    pdf_canvas.setFont("Helvetica-Bold", 9)
    for i in keys:
        pdf_canvas.drawString(keys[i][0]+min_x, keys[i][1]-min_y, i)

    def acres_to_hectares_and_ares(acres):
        total_hectares = acres * 0.40468564224
        whole_hectares = int(total_hectares)
        remaining_hectares = total_hectares - whole_hectares
        ares = remaining_hectares * 100
        return whole_hectares, ares

    def add_all_area():
        a=0
        for i in data['subdivision_list']:
            a += data['subdivision_list'][i][2] * 10.7636 / 435.6 / 100
        hectares, ares = acres_to_hectares_and_ares(a)
        return f"{hectares} hectares {ares:.2f} ares"

    scale = func.calculate_scale_ratio([pnt_wrld['a']['lat'],pnt_wrld['a']['lon']],[pnt_wrld['b']['lat'],pnt_wrld['b']['lon']],[round(pnt_pdf['a']['x']),round(pnt_pdf['a']['y'])],[round(pnt_pdf['b']['x']),round(pnt_pdf['b']['y'])])
    area = add_all_area()
    pdf_canvas.setFillColor((0,0,0))
    pdf_canvas.setFont("Helvetica-Bold", 13)
    pdf_canvas.drawString(x=page_margin+400,y=height-40,text="Survey No: "+data['Survey_No'])
    pdf_canvas.drawString(x=page_margin+400,y=height-60,text="Scale: 1:"+f"{round(scale)}")
    pdf_canvas.drawString(x=page_margin+400,y=height-80,text="Area: "+area)
    pdf_canvas.drawString(x=page_margin+40,y=height-100,text=data['Village']+" | "+data['Taluk']+" | "+data['District'])

    pdf_canvas.save()
    return {"Scale":round(scale), "Area":area}

def generatepdfpage2(data,file_name):
    keys = {}
    pnts = {}

    for i in data['duppoints']:
        keys[i['key']] = [i['latitude']*1,i['longitude']*1]

    for i in data['points']:
        pnts[i['key']]={"lat":i["latitude"],"lon":i["longitude"]}

    page_margin = 20
    dig_padding = 10
    top_marg = 100

    min_x=595.27
    min_y=841.89

    transform_mem = []
    for i in keys:
        transform_mem.append(keys[i])
   
    subdiv_trans_mem = []
    for i,e in data['subdivision_list'].items():
        subdiv_trans_mem.append(e[0])
    temp = transform_mem+subdiv_trans_mem
    temp,scale = pos.resize_points_to_canvas(temp,[595.27-2*page_margin, 841.89-(2*page_margin + top_marg)])
    transform_mem = temp[:len(transform_mem)]
    subdiv_trans_mem = temp[-len(subdiv_trans_mem):]

    for i in keys:
        k=transform_mem.pop(0)
        if min_x > k[0]-page_margin:
            min_x = k[0]-page_margin
        if min_y > k[1]+page_margin:
            min_y = k[1]+page_margin
        keys[i] = [k[0]-page_margin,k[1]+page_margin]

    #pdf
    pdf_canvas = canvas.Canvas(file_name)
    width, height = A4

    if min_x < page_margin:
        min_x = page_margin - min_x
    else:
        min_x = 0

    if min_y > height-page_margin:
        min_y = min_y - height-page_margin
    else:
        min_y = 0


    max_length=max(item["coordinates"] for item in data['lines'])
    pnt_wrld = {
        "a":pnts[max_length[0]],
        "b":pnts[max_length[1]]
    }
    pnt_pdf = {
        "a":{
            "x": keys[max_length[0]][0]+40-10,
            "y": keys[max_length[0]][1]-10,
        },
        "b":{
            "x": keys[max_length[1]][0]+40-10,
            "y": keys[max_length[1]][1]-10,
        }
    }


    #images
    image = sat.get_sat_img(pnt_wrld,pnt_pdf)
    image = cv2.addWeighted( image, 0.8, image, 0, 0)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    image_buffer = BytesIO()
    pil_image.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    # pdf_canvas.drawImage(ImageReader(image_buffer), x=page_margin-dig_padding, y=page_margin-dig_padding,mask='auto')
    pdf_canvas.drawImage(logo, x=page_margin+10, y=height-85, width = 150*2, height= 35*2,mask='auto')


    #margin
    page_margin -= dig_padding
    pdf_canvas.setStrokeColorRGB(0, 0, 0)
    pdf_canvas.setLineWidth(1)

    pdf_canvas.line(page_margin,page_margin,width-(page_margin),page_margin)
    pdf_canvas.line(width-(page_margin),page_margin,width-page_margin,height-page_margin)
    pdf_canvas.line(width-page_margin,height-page_margin,page_margin,height-page_margin)
    pdf_canvas.line(page_margin,height-page_margin,page_margin,page_margin)

    pdf_canvas.line(page_margin,height-(page_margin + top_marg),width-(page_margin),height-(page_margin + top_marg))

    pdf_canvas.setFont("Helvetica-Bold", 11)

    for i in data['lines']:
        cord = i['coordinates']
        dashes_pattern = [int(val) for val in i["dashes"].replace("[", "").replace("]", "").split() if val.isdigit()][:2]
        stk = int(i["strokewidth"])
        pdf_canvas.setLineWidth(stk)
        pdf_canvas.setFillColor(Color(2/255, 125/255, 220/255)) 
        if stk == 3:
            pdf_canvas.setStrokeColorRGB(207/255, 255/255, 0/255)
        elif stk == 1:
            pdf_canvas.setStrokeColorRGB(149/255, 11/255, 220/255)
        
        if len(dashes_pattern) % 2 == 0:
            pdf_canvas.setDash(*dashes_pattern[:2])
        if dashes_pattern != [9, 0]:
            pdf_canvas.setStrokeColorRGB(0.5,0.5,0.5)

        x1=int(keys[i['coordinates'][1]][0]+min_x)
        y1=int(keys[i['coordinates'][1]][1]-min_y)
        x2=int(keys[i['coordinates'][0]][0]+min_x)
        y2=int(keys[i['coordinates'][0]][1]-min_y)

        x1_=(pnts[i['coordinates'][1]]['lat'])
        y1_=(pnts[i['coordinates'][1]]['lon'])
        x2_=(pnts[i['coordinates'][0]]['lat'])
        y2_=(pnts[i['coordinates'][0]]['lon'])

        pdf_canvas.line(x1,y1,x2,y2)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        text_x = (x1 + x2) / 2  # Middle of the line
        text_y = (y1 + y2) / 2 + 10  # Slightly above the line
        pdf_canvas.saveState()
        pdf_canvas.translate(text_x, text_y)
        pdf_canvas.rotate(angle)
        pdf_canvas.drawString(0, 0, f"{func.haversine(x1_,y1_,x2_,y2_)*1000:.1f}")
        pdf_canvas.restoreState()

    #write subdiv
    subdivs_lst_cntr = 0
    for i in data['subdivision_list']:
        subdiv_cord = subdiv_trans_mem[subdivs_lst_cntr]
        pdf_canvas.setFont("Helvetica-Bold", 13)
        pdf_canvas.setFillColor((79/255,190/255,23/255))
        pdf_canvas.drawString(x=subdiv_cord[0],y=subdiv_cord[1],text=i)
        pdf_canvas.setFont("Helvetica-Bold", 9)
        pdf_canvas.setFillColor((79/255,190/255,23/255))
        area = (data['subdivision_list'][i][2] * 10.7636) / 435.6 / 100
        tmp_st = f"{area:.2f}"
        pdf_canvas.drawString(x=subdiv_cord[0] - (len(tmp_st)*1),y=subdiv_cord[1]-10,text=tmp_st)
        subdivs_lst_cntr += 1

    pdf_canvas.setFillColor(Color(239/255, 88/255, 125/255)) 
    pdf_canvas.setFont("Helvetica-Bold", 9)
    for i in keys:
        pdf_canvas.drawString(keys[i][0]+min_x, keys[i][1]-min_y, i)

    def acres_to_hectares_and_ares(acres):
        total_hectares = acres * 0.40468564224
        whole_hectares = int(total_hectares)
        remaining_hectares = total_hectares - whole_hectares
        ares = remaining_hectares * 100
        return whole_hectares, ares

    def add_all_area():
        a=0
        for i in data['subdivision_list']:
            a += data['subdivision_list'][i][2] * 10.7636 / 435.6 / 100
        hectares, ares = acres_to_hectares_and_ares(a)
        return f"{hectares} hectares {ares:.2f} ares"

    pdf_canvas.setFillColor((0,0,0))
    pdf_canvas.setFont("Helvetica-Bold", 13)
    pdf_canvas.drawString(x=page_margin+400,y=height-40,text="Survey No: "+data['Survey_No'])
    pdf_canvas.drawString(x=page_margin+400,y=height-60,text="Scale: 1:"+f"{round(func.calculate_scale_ratio([pnt_wrld['a']['lat'],pnt_wrld['a']['lon']],[pnt_wrld['b']['lat'],pnt_wrld['b']['lon']],[round(pnt_pdf['a']['x']),round(pnt_pdf['a']['y'])],[round(pnt_pdf['b']['x']),round(pnt_pdf['b']['y'])]))}")
    pdf_canvas.drawString(x=page_margin+400,y=height-80,text="Area: "+add_all_area())
    pdf_canvas.drawString(x=page_margin+40,y=height-100,text=data['Village']+" | "+data['Taluk']+" | "+data['District'])

    pdf_canvas.save()
