import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import cv2
import matplotlib.pyplot as plt

# Recreate the model architecture
base_model = tf.keras.applications.MobileNetV2(input_shape=(128, 128, 3),
                                               include_top=False,
                                               weights='imagenet')

base_model.trainable = False

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu'),
    layers.Dense(9, activation='softmax')  # Adjust the number of classes if needed
])

# Build the model by passing a sample input shape
model.build((None, 128, 128, 3))

# Load the model weights
model.load_weights('model.weights.h5')
print("Model weights loaded")

# Load class names
with open('class_names.txt', 'r') as f:
    class_names = [line.strip() for line in f.readlines()]

# Function to preprocess the image
def preprocess_image(img_path):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB
    img = cv2.resize(img, (128, 128))  # Resize to match model's expected input size
    img = img / 255.0  # Normalize pixel values to [0, 1]
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    return img

def visualize_image(img_path, prediction, class_names):
    img = cv.imread(img_path)
    img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    plt.imshow(img_rgb)
    plt.title(f"Predicted: {class_names[np.argmax(prediction)]}, Confidence: {np.max(prediction):.2f}")
    plt.show()

# Example image path
img_path = r'C:\Users\ronar\Desktop\Programming\AI-Based Skin Disease Diagnosis Tool\Dataset\archive\skin-disease-datasaet\test_set\FU-ringworm\21_FU-ringworm (5).jpg'

# Preprocess the image
img = preprocess_image(img_path)

# Show the image uploaded for verification
plt.imshow(cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB))
plt.title('Test Image')
plt.show()

# Perform prediction
predictions = model.predict(img)

# Interpret the predictions
predicted_class_index = np.argmax(predictions)
predicted_class = class_names[predicted_class_index]
print(f'Predicted class: {predicted_class}')
print(f'Prediction confidence: {predictions[0][predicted_class_index]}')
print('All class probabilities:', predictions[0])

# Debugging: Print all class probabilities
for i, class_name in enumerate(class_names):
    print(f'{class_name}: {predictions[0][i]:.4f}')