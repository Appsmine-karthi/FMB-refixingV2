import cairosvg
from PyPDF2 import PdfMerger
import os
def page2pdfgenerator(svgfile,page1pdf,page2pdf,output_pdf):
    if os.path.exists(output_pdf):
        os.remove(output_pdf)
    # List of SVG files to combine
    svg_files = [svgfile]

    # Temporary list to store generated PDFs
    pdf_files = ["Mobile_Land_Survey_front_Page.pdf",page1pdf,page2pdf]

    # Convert each SVG to a temporary PDF
    for i, svg_file in enumerate(svg_files):
        pdf_file = f"temp_page_{i + 1}.pdf"
        cairosvg.svg2pdf(file_obj=open(svg_file, "rb"), write_to=pdf_file)
        pdf_files.append(pdf_file)

    merger = PdfMerger()

    for pdf_file in pdf_files:
        merger.append(pdf_file)

    merger.write(output_pdf)
    merger.close()
    print(f"Combined PDF saved as {output_pdf}")
