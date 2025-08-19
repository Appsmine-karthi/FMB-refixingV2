import cairosvg
from PyPDF2 import PdfMerger
import os
import tempfile
import shutil

def page2pdfgenerator(svgfile, page1pdf, page2pdf, output_pdf):
    # Ensure output directory exists
    output_dir = os.path.dirname(output_pdf)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Remove existing output file if it exists
    if os.path.exists(output_pdf):
        try:
            os.remove(output_pdf)
        except OSError as e:
            print(f"Warning: Could not remove existing output file: {e}")
    
    # List of SVG files to combine
    svg_files = [svgfile]
    
    # Get the directory of the current script to find the hardcoded PDF
    script_dir = os.path.dirname(os.path.abspath(__file__))
    front_page_pdf = os.path.join(script_dir, "Mobile_Land_Survey_front_Page.pdf")
    
    # Validate that all required PDF files exist
    required_pdfs = [front_page_pdf, page1pdf, page2pdf]
    for pdf_file in required_pdfs:
        if not os.path.exists(pdf_file):
            raise FileNotFoundError(f"Required PDF file not found: {pdf_file}")
    
    # Temporary list to store generated PDFs
    pdf_files = [front_page_pdf, page1pdf, page2pdf]
    
    # Temporary files to clean up later
    temp_pdf_files = []
    
    try:
        # Convert each SVG to a temporary PDF
        for i, svg_file in enumerate(svg_files):
            if not os.path.exists(svg_file):
                raise FileNotFoundError(f"SVG file not found: {svg_file}")
            
            # Use tempfile module for better temporary file handling
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                pdf_file = temp_file.name
                temp_pdf_files.append(pdf_file)
            
            # Use context manager to ensure file is properly closed
            with open(svg_file, "rb") as svg_f:
                try:
                    cairosvg.svg2pdf(file_obj=svg_f, write_to=pdf_file)
                    print(f"Successfully converted SVG to PDF: {pdf_file}")
                except Exception as e:
                    print(f"Error converting SVG to PDF: {e}")
                    raise
            
            pdf_files.append(pdf_file)
        
        # Merge PDFs
        merger = PdfMerger()
        
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                try:
                    merger.append(pdf_file)
                    print(f"Added PDF to merger: {pdf_file}")
                except Exception as e:
                    print(f"Error adding PDF to merger: {e}")
                    raise
            else:
                print(f"Warning: PDF file not found: {pdf_file}")
        
        merger.write(output_pdf)
        merger.close()
        
        print(f"Successfully generated: {output_pdf}")
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        # Clean up any partial output
        if os.path.exists(output_pdf):
            try:
                os.remove(output_pdf)
            except OSError:
                pass
        raise
    
    finally:
        # Clean up temporary PDF files
        for temp_file in temp_pdf_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"Cleaned up temporary file: {temp_file}")
                except OSError as e:
                    print(f"Warning: Could not remove temporary file {temp_file}: {e}")