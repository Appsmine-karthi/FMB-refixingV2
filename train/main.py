from PIL import Image, ImageDraw, ImageFont
import os

font = ImageFont.truetype("Helvetica.ttf", 100)
chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

os.makedirs("dataset", exist_ok=True)
for char in chars:
    img = Image.new("L", (100, 100), color=255)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), char, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((100-w)//2, (100-h)//2), char, fill=0, font=font)
    img.save(f"dataset/{char}.png")
