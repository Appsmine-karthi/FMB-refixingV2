from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
import numpy as np
import cv2
import os

# Load dataset
X, y = [], []
label_map = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

for i, char in enumerate(label_map):
    img = cv2.imread(f"dataset/{char}.png", cv2.IMREAD_GRAYSCALE)
    img = img / 255.0
    X.append(img.reshape(100, 100, 1))
    y.append(i)

X = np.array(X)
y = to_categorical(y)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

# Simple CNN
model = Sequential([
    Conv2D(16, (3, 3), activation='relu', input_shape=(100, 100, 1)),
    MaxPooling2D(),
    Conv2D(32, (3, 3), activation='relu'),
    MaxPooling2D(),
    Flatten(),
    Dense(64, activation='relu'),
    Dense(len(label_map), activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=10)

model.save("model.h5")