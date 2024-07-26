Skin Disease Diagnosis Tool

This project is a web application that leverages machine learning to diagnose skin diseases from uploaded images. The application is built using Flask for the backend, TensorFlow/Keras for the machine learning model, and OpenCV for image preprocessing. The frontend is designed with HTML, CSS, and JavaScript.


Features

- Image Upload: Users can upload images of skin conditions for diagnosis.
- Machine Learning Model: The application uses a pre-trained MobileNetV2 model with custom layers for predicting skin diseases.
- Secure Database: User information is stored securely in a database.


Project Structure


.
├── app.py
├── requirements.txt
├── static
│   ├── css
│   │   └── styles.css
│   ├── images
│   └── js
│       └── scripts.js
├── templates
│   ├── index.html
│   ├── signup.html
│   ├── login.html
│   └── diagnosis.html
├── model
│   └── skin_disease_model.h5
├── utils
│   └── preprocess.py
└── README.md


Installation

1. Clone the repository:

   git clone https://github.com/yourusername/skin-disease-diagnosis.git
   cd skin-disease-diagnosis
   

2. Create and activate a virtual environment:

   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   

3. Install the required packages:

   pip install -r requirements.txt
   

4. Run the Flask application:

   flask run
   

Usage

1. Home Page: The landing page where users can navigate to diagnose their skin condition.
2. Diagnosis: Users can upload an image of a skin condition to get a diagnosis.


Model Training

The machine learning model is trained using the MobileNetV2 architecture with custom layers. The dataset is stored locally, and the training involves data preprocessing, augmentation, and normalization. The model is then saved as `skin_disease_model.h5` for use in the application.


Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

Contact

For any inquiries, please contact ronardbotchway@gmail.com

