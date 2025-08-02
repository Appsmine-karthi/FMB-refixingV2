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

# print(pdfTemp)
# print(logoIcon)

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

def generatecad(data,id):
    inputsvg = "temp/"+id+".svg"
    inputpdf = "temp/"+id+"_2.pdf"
    tempsvg = "temp/"+id+"_temp.svg"
    dxf1_file = "temp/"+id+"_1.dxf"
    dxf2_file = "temp/"+id+"_2.dxf"
    outputcad = "temp/"+id+".dxf"
    cadname = id+".dxf"
    pdftocad(inputpdf,tempsvg,inputsvg,dxf1_file,dxf2_file,outputcad)
    s3_url = uploadtos3(outputcad,cadname)
    return s3_url
    # data = {'District': 'Namakkal', 'Taluk': 'Tiruchengode', 'Village': 'Avinasipatty', 'Survey_No': '77', 'duppoints': [{'id': 1, 'latitude': 827494.498, 'longitude': 1264455.491, 'key': '1', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 2, 'latitude': 827530.166, 'longitude': 1264619.335, 'key': '2', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 3, 'latitude': 827576.629, 'longitude': 1264613.475, 'key': '3', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 4, 'latitude': 827721.046, 'longitude': 1264513.002, 'key': '4', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 5, 'latitude': 827714.822, 'longitude': 1264455.535, 'key': '5', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 6, 'latitude': 827692.447, 'longitude': 1264458.221, 'key': '6', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 7, 'latitude': 827579.832, 'longitude': 1264495, 'key': '7', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 8, 'latitude': 827789.169, 'longitude': 1264411.168, 'key': '8', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 9, 'latitude': 827802.123, 'longitude': 1264443.571, 'key': '9', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 10, 'latitude': 827805.169, 'longitude': 1264496.391, 'key': '10', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 11, 'latitude': 827813.72, 'longitude': 1264532.828, 'key': '11', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 12, 'latitude': 827758.085, 'longitude': 1264548.711, 'key': '12', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 13, 'latitude': 827733.141, 'longitude': 1264558.61, 'key': '13', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 14, 'latitude': 827729.353, 'longitude': 1264548.583, 'key': '14', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 15, 'latitude': 827620.893, 'longitude': 1264593.433, 'key': '15', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 16, 'latitude': 827459.404, 'longitude': 1264471.989, 'key': 'A', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 17, 'latitude': 827556.005, 'longitude': 1264421.268, 'key': 'B', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 18, 'latitude': 827717.395, 'longitude': 1264428.882, 'key': 'C', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 19, 'latitude': 827810.666, 'longitude': 1264518.889, 'key': 'D', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 20, 'latitude': 827805.161, 'longitude': 1264535.271, 'key': 'E', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 21, 'latitude': 827602.429, 'longitude': 1264603.333, 'key': 'F', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}], 'points': [{'id': 1, 'latitude': 11.423039504453419, 'longitude': 78.0009188360617, 'key': '1', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 2, 'latitude': 11.424515881038499, 'longitude': 78.0012609398117, 'key': '2', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 3, 'latitude': 11.424458605518426, 'longitude': 78.00168572520604, 'key': '3', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 4, 'latitude': 11.423537652168601, 'longitude': 78.00299823918228, 'key': '4', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 5, 'latitude': 11.423019241764244, 'longitude': 78.00293579633767, 'key': '5', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 6, 'latitude': 11.423045593027265, 'longitude': 78.00273121730017, 'key': '6', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 7, 'latitude': 11.423388321347835, 'longitude': 78.0017037821549, 'key': '7', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 8, 'latitude': 11.422611569784317, 'longitude': 78.00361218392085, 'key': '8', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 9, 'latitude': 11.422902995693748, 'longitude': 78.00373385052102, 'key': '9', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 10, 'latitude': 11.423379737739277, 'longitude': 78.00376675975996, 'key': '10', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 11, 'latitude': 11.423708007820226, 'longitude': 78.00384850898287, 'key': '11', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 12, 'latitude': 11.423856676031642, 'longitude': 78.00334071422702, 'key': '12', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 13, 'latitude': 11.42394841302349, 'longitude': 78.00311330239428, 'key': '13', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 14, 'latitude': 11.423858215623643, 'longitude': 78.00307766925994, 'key': '14', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 15, 'latitude': 11.424273442077554, 'longitude': 78.002089040564, 'key': '15', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 16, 'latitude': 11.423191800588633, 'longitude': 78.00059913756809, 'key': 'A', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 17, 'latitude': 11.42272466739066, 'longitude': 78.00147864832914, 'key': 'B', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 18, 'latitude': 11.42277828525801, 'longitude': 78.00295681579989, 'key': 'C', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 19, 'latitude': 11.423582407987144, 'longitude': 78.00381922644071, 'key': 'D', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 20, 'latitude': 11.423730879901528, 'longitude': 78.00377038676082, 'key': 'E', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}, {'id': 21, 'latitude': 11.424364582255095, 'longitude': 78.00192095041828, 'key': 'F', 'latstatus': 'notmodified', 'longstatus': 'notmodified'}], 'lines': [{'coordinates': ['E', 'C'], 'dashes': '[ 30 10 1 3 1 3 1 10 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['E', 'F'], 'dashes': '[ 30 10 1 3 1 3 1 10 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['B', 'F'], 'dashes': '[ 30 10 1 3 1 3 1 10 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['A', 'B'], 'dashes': '[ 30 10 1 3 1 3 1 10 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['A', 'F'], 'dashes': '[ 30 10 1 3 1 3 1 10 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['F', 'C'], 'dashes': '[ 30 10 1 3 1 3 1 10 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['C', 'B'], 'dashes': '[ 30 10 1 3 1 3 1 10 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['C', 'D'], 'dashes': '[ 30 10 1 3 1 3 1 10 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['E', 'D'], 'dashes': '[ 30 10 1 3 1 3 1 10 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['F', '15'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['15', '14'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['14', '13'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['13', '12'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['12', 'E'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['E', '11'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['11', 'D'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['D', '10'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['10', '9'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['9', '8'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['8', 'C'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['C', '5'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['5', '6'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['6', '7'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['7', 'B'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['B', '1'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['1', 'A'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['A', '2'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['2', '3'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['3', 'F'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '3'}, {'coordinates': ['F', '7'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['14', '4'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['4', '5'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['4', '10'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}, {'coordinates': ['5', '9'], 'dashes': '[ 9 0 ] 1', 'length': 660.3205757314188, 'strokewidth': '1'}]}
    # Prepare a dictionary for quick lookup of points by their key
    # point_dict = {point['key']: (int(point['latitude'])-827200,1200-(int(point['longitude'])-1263800)) for point in data['duppoints']}
    # print(point_dict)
    # # Create an SVG drawing
    # dwg = svgwrite.Drawing(outputsvg, profile='tiny', size=("790px", "1120px"))
    # dwg.viewbox(0, 0, 790, 1120)

    # # Call the function to draw the table
    # # Draw lines based on the 'lines' section
    # def scale_point(point, scale_factor, center=(0, 0)):
    #     return (
    #         center[0] + (point[0] - center[0]) * scale_factor,
    #         center[1] + (point[1] - center[1]) * scale_factor,
    #     )
    # for line in data['lines']:
    #     coordinates = line['coordinates']
    #     start = point_dict.get(coordinates[0])
    #     end = point_dict.get(coordinates[1])
    #     scale_factor = 1
    #     if start and end:
    #         center_of_scaling = (300, 300)  # Or set to a specific point
            
    #         # Scale start and end points
    #         start = scale_point(start, scale_factor, center=center_of_scaling)
    #         end = scale_point(end, scale_factor, center=center_of_scaling)
    #         # Line properties
    #         stroke_width = int(line['strokewidth']) if 'strokewidth' in line else 1
            
    #         # Calculate the length of the line
    #         length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            
    #         # Calculate the midpoint of the line
    #         midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
            
    #         # Calculate the angle of the line in degrees
    #         angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
            
    #         print("data ", start, end, stroke_width, "Length:", length, "Angle:", angle)
            
    #         # Draw the line
    #         dwg.add(dwg.line(
    #             start=start,
    #             end=end,
    #             stroke='#000000',
    #             stroke_width=stroke_width,
    #         ))
            
    #         # # Add text at the midpoint displaying the line's length, rotated along the line's angle
    #         # text = dwg.text(
    #         #     f"{length:.2f}",  # Format the length to 2 decimal places
    #         #     insert=midpoint,
    #         #     fill='red',
    #         #     font_size=10,
    #         #     text_anchor="middle",  # Center the text horizontally
    #         #     # dominant_baseline="central"  # Center the text vertically
    #         # )
            
    #         # Apply rotation transformation to align text with the line's angle
    #         # text.rotate(angle, center=midpoint)
            
    #         # # Add the rotated text to the SVG
    #         # dwg.add(text)
    # # Save the SVG file
    # dwg.save()
    # svgtocad(outputsvg,outputcad)
    # cadname = data['Village']+"_"+data['Taluk']+"_"+data['District']+"_"+data['Survey_No']+".dxf"
    # s3_url = uploadtos3(outputcad,cadname)
    # return s3_url

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

    return outputpdf