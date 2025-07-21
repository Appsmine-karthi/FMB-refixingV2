import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Define character label map
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
reverse_map = {i: char for i, char in enumerate(CHARS)}

# Load the trained model
model = load_model("model.h5")

def preprocess_image(img_path, size=100):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (size, size))
    img = img / 255.0  # Normalize
    return img.reshape(1, size, size, 1)

def predict_character(img_path):
    img = preprocess_image(img_path)
    pred = model.predict(img)
    predicted_class = np.argmax(pred)
    confidence = np.max(pred)
    return reverse_map[predicted_class], confidence

# Example usage
if __name__ == "__main__":
    img_path = "image.png"  # Replace with your test image
    character, confidence = predict_character(img_path)
    print(f"Predicted: {character}, Confidence: {confidence:.2f}")
