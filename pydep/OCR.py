from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import easyocr
import numpy as np
import cv2
from io import BytesIO
import torch

app = FastAPI()

# Check if GPU is available
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

# Initialize the OCR reader globally for better performance with GPU support
reader = easyocr.Reader(['en'], recog_network='english_g2', gpu=(device == 'cuda'))

@app.post('/ocr')
async def ocr(image: UploadFile = File(...)):
    try:
        # Check if image file is provided
        if not image:
            raise HTTPException(status_code=400, detail="No image file provided")
        
        # Read image file into memory
        image_bytes = await image.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image_cv is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Perform OCR with GPU acceleration
        results = reader.readtext(image_cv, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        
        text_results = []
        for result in results:
            bbox = result[0]
            bbox_list = [[float(coord) for coord in point] for point in bbox]
            
            text_results.append({
                'text': result[1]
            })

        return JSONResponse({
            'success': True,
            'results': text_results,
            'device_used': device
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
