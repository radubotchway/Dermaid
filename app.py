import os
import numpy as np
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Assuming you have loaded your model and class names
# model = ...
# class_names = ...

# Dictionary containing disease information
disease_info = {
    'Disease1': {
        'description': 'Description of Disease 1.',
        'recommendations': 'Follow-up recommendations for Disease 1.',
        'treatment': 'Treatment options for Disease 1.',
        'advice': 'Advice on consulting a healthcare professional for Disease 1.'
    },
    'Disease2': {
        'description': 'Description of Disease 2.',
        'recommendations': 'Follow-up recommendations for Disease 2.',
        'treatment': 'Treatment options for Disease 2.',
        'advice': 'Advice on consulting a healthcare professional for Disease 2.'
    },
    # Add more diseases as needed
}

def preprocess_image(filepath):
    # Add your image preprocessing code here
    pass

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(success=False, error='No file part')

    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, error='No selected file')

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)

        img = preprocess_image(filepath)
        prediction = model.predict(img)
        index = np.argmax(prediction)
        result = class_names[index]
        
        info = disease_info.get(result, {})
        return jsonify(success=True, prediction=result, info=info)

    return jsonify(success=False, error='Unknown error')

@app.route('/upload.html', methods=['GET'])
def upload_page():
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
