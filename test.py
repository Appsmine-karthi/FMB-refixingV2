import os
from dotenv import load_dotenv
load_dotenv()
pdfTemp = os.getenv("PDF_TEMP")
logoIcon = os.getenv("LOGO_ICON")

print(pdfTemp)
print(logoIcon)