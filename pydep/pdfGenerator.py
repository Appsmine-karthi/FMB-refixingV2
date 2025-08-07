import svgwrite
import base64
import math
from page2pdfgenerator import page2pdfgenerator
from sat_on_pdf.main import generatepdfpage1,generatepdfpage2

import os
from dotenv import load_dotenv
load_dotenv()
pdfTemp = os.getenv("PDF_TEMP")
logoIcon = os.getenv("LOGO_ICON")
S3SatDir = os.getenv("S3_SAT_PDF_DIR")

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_REGION      = os.getenv("S3_REGION")
BUCKET_NAME    = os.getenv("BUCKET_NAME")

import boto3
from botocore.exceptions import NoCredentialsError

def OutputFileToS3(LocalFileName):
    file_name = os.path.basename(LocalFileName)
    s3_key = f"fmb_refixing/{S3SatDir}{file_name}" if S3SatDir else file_name

    # Create S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=S3_REGION
    )

    try:
        s3.upload_file(LocalFileName, BUCKET_NAME, s3_key)
        s3_url = f"https://{BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        return s3_url
    except FileNotFoundError:
        print(f"The file {LocalFileName} was not found.")
        return None
    except NoCredentialsError:
        print("Credentials not available for AWS S3.")
        return None
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None



def img_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")
def draw_table(dwg,dup_point,point):
    x_offset = 50  # X starting position for table
    y_offset = 180  # Y starting position for table
    col_width = 110  # Width of each column
    col_width1 = 140
    row_height = 30  # Height of each row
    header_row_height = 30  # Height of the header row

    # Add the header row
    dwg.add(dwg.rect(insert=(x_offset, y_offset), size=(col_width, row_height), fill='white', stroke='black'))
    dwg.add(dwg.rect(insert=(x_offset + col_width, y_offset), size=(col_width, row_height), fill='white', stroke='black'))
    dwg.add(dwg.rect(insert=(x_offset + 2 * col_width, y_offset), size=(col_width, row_height), fill='white', stroke='black'))
    dwg.add(dwg.rect(insert=(x_offset + 3 * col_width, y_offset), size=(col_width1, row_height), fill='white', stroke='black'))
    dwg.add(dwg.rect(insert=(x_offset + 4 * col_width+30, y_offset), size=(col_width1, row_height), fill='white', stroke='black'))
    dwg.add(dwg.text('Key', insert=(x_offset + 10, y_offset + 25), font_size=12, fill='black'))
    dwg.add(dwg.text('UTM X', insert=(x_offset + col_width + 10, y_offset + 25), font_size=12, fill='black'))
    dwg.add(dwg.text('UTM Y', insert=(x_offset + 2 * col_width + 10, y_offset + 25), font_size=12, fill='black'))
    dwg.add(dwg.text('Latitude', insert=(x_offset + 3 *col_width + 30, y_offset + 25), font_size=12, fill='black'))
    dwg.add(dwg.text('Lognitude', insert=(x_offset + 4 * col_width + 50, y_offset + 25), font_size=12, fill='black'))

    # Add rows with the data
    y_offset += header_row_height  # Move down after header
    for idx, (label, (x, y)) in enumerate(dup_point.items()):
        row_y_pos = y_offset + idx * row_height
        dwg.add(dwg.rect(insert=(x_offset, row_y_pos), size=(col_width, row_height), fill='white', stroke='black'))
        dwg.add(dwg.text(label, insert=(x_offset + 10, row_y_pos + 20), font_size=12, fill='#FF0000'))
        
        dwg.add(dwg.rect(insert=(x_offset + col_width, row_y_pos), size=(col_width, row_height), fill='white', stroke='black'))
        dwg.add(dwg.text(str(x), insert=(x_offset + col_width + 10, row_y_pos + 20), font_size=12, fill='black'))
        
        dwg.add(dwg.rect(insert=(x_offset + 2 * col_width, row_y_pos), size=(col_width, row_height), fill='white', stroke='black'))
        dwg.add(dwg.text(str(y), insert=(x_offset + 2 * col_width + 10, row_y_pos + 20), font_size=12, fill='black'))
    for idx, (label, (x, y)) in enumerate(point.items()):
        row_y_pos = y_offset + idx * row_height
        dwg.add(dwg.rect(insert=(x_offset + 3 * col_width, row_y_pos), size=(col_width1, row_height), fill='white', stroke='black'))
        dwg.add(dwg.text(str(x)[:14], insert=(x_offset + 3 * col_width + 10, row_y_pos + 20), font_size=12, fill='black'))
        
        dwg.add(dwg.rect(insert=(x_offset + 4 * col_width+30, row_y_pos), size=(col_width1, row_height), fill='white', stroke='black'))
        dwg.add(dwg.text(str(y)[:14], insert=(x_offset + 4* col_width + 40, row_y_pos + 20), font_size=12, fill='black'))

def generatepdf(data,id):
    outputsvg = pdfTemp+id+".svg"
    page1pdf = pdfTemp+id+"_1.pdf"
    page2pdf = pdfTemp+id+"_2.pdf"
    outputpdf = pdfTemp+id+".pdf"
    scaleandarea = generatepdfpage1(data,page1pdf)
    generatepdfpage2(data,page2pdf)
    dup_point = {point['key']: (point['latitude'],point['longitude']) for point in data['duppoints']}
    point = {point['key']: (point['latitude'],point['longitude']) for point in data['points']}
    dwg = svgwrite.Drawing(outputsvg, profile='tiny', size=("790px", "1120px"))
    dwg.viewbox(0, 0, 790, 1120)
    dwg.add(dwg.line(
            start=(4,4),
            end=(4,1116),
            stroke='#000000',
            stroke_width=3,
            # stroke_dasharray=dash_array
        ))
    dwg.add(dwg.line(
            start=(4,4),
            end=(786,4),
            stroke='#000000',
            stroke_width=3,
            # stroke_dasharray=dash_array
        ))
    dwg.add(dwg.line(
            start=(4,1116),
            end=(786,1116),
            stroke='#000000',
            stroke_width=3,
            # stroke_dasharray=dash_array
        ))
    dwg.add(dwg.line(
            start=(786,4),
            end=(786,1116),
            stroke='#000000',
            stroke_width=3,
            # stroke_dasharray=dash_array
        ))
    dwg.add(dwg.line(
            start=(4,140),
            end=(786,140),
            stroke='#000000',
            stroke_width=3,
            # stroke_dasharray=dash_array
        ))

    dwg.add(dwg.text(
        "Survey No: "+data['Survey_No'],  # Text content
        insert=(530, 50),  fill="#000000",  
        font_size="15px",  font_family="Arial", 
        # text_anchor="middle"
    ))
    dwg.add(dwg.text(
        "Scale: 1:"+str(scaleandarea['Scale']),  # Text content
        insert=(530, 90),  fill="#000000",  
        font_size="15px",  font_family="Arial", 
        # text_anchor="middle"
    ))
    dwg.add(dwg.text(
        "Area: "+scaleandarea['Area'],  # Text content
        insert=(530, 130),  fill="#000000",  
        font_size="15px",  font_family="Arial", 
        # text_anchor="middle"
    ))
    dwg.add(dwg.text(
        data['Village']+", "+data['Taluk']+", "+data['District']+".",  # Text content
        insert=(30, 130),  fill="#000000",  
        font_size="15px",  font_family="Arial", 
        # text_anchor="middle"
    ))
    dwg.add(dwg.text(
        "My Property",  # Text content
        insert=(110, 80),  fill="#000000",  
        font_size="40px",  font_family="serif", font_weight="bold" 
        # text_anchor="middle"
    ))
    image_data = img_to_base64(logoIcon)
    # Add the image as base64-encoded data to the SVG
    dwg.add(dwg.image(href="data:image/png;base64," + image_data, insert=(20, 20), size=(90, 90)))
    draw_table(dwg,dup_point,point)
    dwg.save()
    page2pdfgenerator(outputsvg,page1pdf,page2pdf,outputpdf)

    S3Url = OutputFileToS3(outputpdf)

    os.remove(outputsvg)
    os.remove(page1pdf )
    os.remove(page2pdf )
    os.remove(outputpdf)

    return S3Url