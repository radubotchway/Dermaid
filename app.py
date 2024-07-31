from flask import Flask, render_template, request, redirect, url_for, jsonify
import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import cv2
import os
# import io
from PIL import Image
from werkzeug.utils import secure_filename
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

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
model.load_weights('model/model.weights.h5')
print("Model weights loaded")

# Load class names
with open('model/class_names.txt', 'r') as f:
    class_names = [line.strip() for line in f.readlines()]

# Dictionary containing disease information
disease_info = {
    'Cellulitis': {
        'description': 'Cellulitis is a common, potentially serious bacterial skin infection. It appears as a swollen, red area of skin that feels hot and tender, and it may spread rapidly.',
        'recommendations': 'Seek medical attention promptly, follow the prescribed antibiotic course, and keep the infected area clean and elevated.',
        'treatment': 'Antibiotics are typically prescribed to treat cellulitis. In severe cases, hospitalization and intravenous antibiotics may be necessary.',
        'advice': 'Consult a healthcare professional immediately if you notice signs of cellulitis, especially if the redness or swelling spreads, you have a fever, or the area becomes numb.'
    },
    'Impetigo': {
        'description': 'Impetigo is a highly contagious bacterial skin infection common in young children. It appears as red sores on the face, especially around a child’s nose and mouth, and on hands and feet.',
        'recommendations': 'Keep the affected area clean, avoid touching or scratching the sores, and maintain good personal hygiene.',
        'treatment': 'Topical or oral antibiotics are used to treat impetigo. Proper hygiene and regular cleaning of the infected area are also important.',
        'advice': 'Consult a healthcare professional for a proper diagnosis and treatment plan if you or your child develops impetigo.'
    },
    'Clear Skin': {
        'description': 'The uploaded skin appears to be clear and healthy.',
        'recommendations': 'No immediate actions are necessary. Maintain good skin hygiene.',
        'treatment': 'None required.',
        'advice': 'If you have any concerns about your skin, consult a healthcare professional.'
    },
    'Athlete-Foot': {
        'description': 'Athlete’s foot is a fungal infection that usually begins between the toes. It commonly occurs in people whose feet have become very sweaty while confined within tight-fitting shoes.',
        'recommendations': 'Keep feet dry, especially between the toes, change socks regularly, and use antifungal powders or sprays as recommended.',
        'treatment': 'Topical antifungal medications are commonly used to treat athlete’s foot. Severe cases may require oral antifungal drugs.',
        'advice': 'See a healthcare professional if the infection does not improve with over-the-counter treatments or if it recurs frequently.'
    },
    'Nail Fungus': {
        'description': 'Nail fungus is a common condition that begins as a white or yellow spot under the tip of your fingernail or toenail. As the fungal infection goes deeper, nail fungus may cause your nail to discolor, thicken, and crumble at the edge.',
        'recommendations': 'Maintain good nail hygiene, keep nails trimmed, and avoid walking barefoot in damp public areas.',
        'treatment': 'Antifungal medications, either topical or oral, are used to treat nail fungus. In severe cases, nail removal may be necessary.',
        'advice': 'Consult a healthcare professional if you notice signs of nail fungus to obtain a proper diagnosis and treatment plan.'
    },
    'Ringworm': {
        'description': 'Ringworm is a common fungal infection that creates a ring-like, red, itchy rash on the skin. It can affect the skin on your body (tinea corporis), scalp (tinea capitis), feet (tinea pedis), or groin (tinea cruris).',
        'recommendations': 'Keep the affected area clean and dry, avoid sharing personal items, and use antifungal creams as directed.',
        'treatment': 'Topical antifungal medications are usually effective in treating ringworm. Severe or persistent infections may require oral antifungal drugs.',
        'advice': 'See a healthcare professional for a proper diagnosis and treatment if the infection does not improve with over-the-counter treatments.'
    },
    'Cutaneous Larva Migrans': {
        'description': 'Cutaneous larva migrans is a skin infection caused by hookworm larvae, resulting in itchy, red, winding rash as the larvae migrate under the skin.',
        'recommendations': 'Avoid walking barefoot on soil or sand, especially in areas where hookworm is common. Keep the affected area clean and avoid scratching.',
        'treatment': 'Antiparasitic medications, such as albendazole or ivermectin, are used to treat cutaneous larva migrans.',
        'advice': 'Consult a healthcare professional if you develop symptoms of cutaneous larva migrans for appropriate treatment.'
    },
    'Chicken Pox': {
        'description': 'Chickenpox is a highly contagious viral infection causing an itchy, blister-like rash on the skin. It primarily affects children, but can be more severe in adults.',
        'recommendations': 'Keep the patient isolated to prevent the spread, maintain good hygiene, and avoid scratching the blisters.',
        'treatment': 'Supportive care, such as antihistamines for itching and paracetamol for fever. In severe cases, antiviral medications may be prescribed.',
        'advice': 'Consult a healthcare professional if the patient is at high risk for complications or if the infection appears severe.'
    },
    'Shingles': {
        'description': 'Shingles is a viral infection causing a painful rash, typically in a single stripe of blisters on one side of the body. It is caused by the reactivation of the varicella-zoster virus, which also causes chickenpox.',
        'recommendations': 'Seek medical attention promptly, keep the rash clean and dry, and avoid contact with pregnant women, infants, and immunocompromised individuals.',
        'treatment': 'Antiviral medications can reduce the severity and duration of shingles if started early. Pain management is also important.',
        'advice': 'Consult a healthcare professional immediately if you suspect shingles for proper diagnosis and treatment to prevent complications.'
    },
}

# Function to preprocess the image
def preprocess_image(img_path):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # converting from BGR to RGB
    img = cv2.resize(img, (128, 128))  # Resize to 128x128 pixels
    img = img / 255.0  # Normalize the image
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    return img

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/index.html')
def index_page():
    return render_template('index.html')

@app.route('/upload.html')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify(success=False, error='No file part')
    
    file = request.files['image']
    if file.filename == '':
        return jsonify(success=False, error='No selected file')
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
        except Exception as e:
            return jsonify(success=False, error=f"Error saving file: {e}")
        
        try:
            img = preprocess_image(filepath)
            prediction = model.predict(img)
            index = np.argmax(prediction)
            result = class_names[index]
        
            # Add disease information to the response
            info = disease_info.get(result, {})
            return jsonify(success=True, prediction=result, info=info)
        except Exception as e:
            return jsonify(success=False, error=f"Error processing image: {e}")

    return jsonify(success=False, error='Unknown error')

@app.route('/faq.html')
def faq():
    return render_template('faq.html')

# @app.route('/download-pdf', methods=['GET'])
# def download_pdf():
#     diagnosis = request.args.get('diagnosis', 'No diagnosis provided')
#     advice = request.args.get('advice', 'No advice provided')
#     recommendations = request.args.get('recommendations', 'No recommendations provided')
#     treatment_options = request.args.get('treatment_options', 'No treatment options provided')

#     buffer = io.BytesIO()
#     c = canvas.Canvas(buffer, pagesize=letter)
#     c.drawString(100, 750, "Diagnosis Report")
#     c.drawString(100, 700, f"Diagnosis: {diagnosis}")
#     c.drawString(100, 650, f"Advice: {advice}")
#     c.drawString(100, 600, f"Recommendations: {recommendations}")
#     c.drawString(100, 550, f"Treatment Options: {treatment_options}")
#     c.save()

#     buffer.seek(0)
#     return send_file(buffer, as_attachment=True, download_name='diagnosis_report.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)