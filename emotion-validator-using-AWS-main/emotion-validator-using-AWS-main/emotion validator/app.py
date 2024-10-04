from flask import Flask, render_template, request, redirect, url_for
import os
import base64
from PIL import Image, ImageDraw, ImageFont
import boto3
from io import BytesIO

app = Flask(__name__)

# AWS Rekognition client setup
rekognition = boto3.client('rekognition', aws_access_key_id='YOUR_ACCESS_KEY',
                           aws_secret_access_key='YOUR_SECRET_ACCESS_KEY',
                           region_name='us-east-1')

font = ImageFont.truetype('arial.ttf', 30)

# Function to process the captured image data
def process_image_data(image_data):
    # Convert the base64-encoded image data to bytes
    image_bytes = base64.b64decode(image_data.split(',')[1])
    # Create a PIL Image object from the bytes
    image = Image.open(BytesIO(image_bytes))
    # Save the image to a temporary file
    file_path = os.path.join('static', 'captured_image.jpg')
    image.save(file_path)
    return file_path

# Function to detect faces and emotions
def detect_faces_and_emotions(image_path: str):
    with open(image_path, 'rb') as image_data:
        response_content = image_data.read()

    rekognition_response = rekognition.detect_faces(
        Image={'Bytes': response_content}, Attributes=['ALL'])

    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    for item in rekognition_response.get('FaceDetails'):
        bounding_box = item['BoundingBox']
        image_width, image_height = image.size
        width = image_width * bounding_box['Width']
        height = image_height * bounding_box['Height']
        left = image_width * bounding_box['Left']
        top = image_height * bounding_box['Top']

        left = int(left)
        top = int(top)
        width = int(width) + left
        height = int(height) + top

        draw.rectangle(((left, top), (width, height)),
                       outline='red', width=3)

        face_emotion_confidence = 0
        face_emotion = None
        for emotion in item.get('Emotions'):
            if emotion.get('Confidence') > face_emotion_confidence:
                face_emotion_confidence = emotion['Confidence']
                face_emotion = emotion.get('Type')

        draw.text((left, top), face_emotion, 'green', font=font)

    # Save the processed image
    result_path = os.path.join('static', 'result_image.jpg')
    image.save(result_path)
    return result_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/choose_option', methods=['POST'])
def choose_option():
    option = request.form.get('option')
    if option == 'upload':
        return redirect(url_for('upload_file'))
    elif option == 'camera':
        return redirect(url_for('capture_from_camera'))
    else:
        return 'Invalid option'

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            # Save the uploaded file to a temporary location
            file_path = os.path.join('static', 'uploaded_image.jpg')
            file.save(file_path)
            # Detect faces and emotions from the uploaded file
            result_image_path = detect_faces_and_emotions(file_path)
            # Display the result
            return redirect(url_for('result', image_path=result_image_path))
    return render_template('upload.html')

@app.route('/result')
def result():
    image_path = request.args.get('image_path')
    return render_template('result.html', result_image=image_path)


@app.route('/capture_from_camera')
def capture_from_camera():
    return render_template('capture.html')

@app.route('/process_image', methods=['POST'])
def process_image():
    if request.method == 'POST':
        image_data = request.json.get('image')
        if image_data:
            # Process the captured image data
            file_path = process_image_data(image_data)
            # Detect faces and emotions from the captured image
            result_image_path = detect_faces_and_emotions(file_path)
            # Return the path to the result image
            return result_image_path
    return 'Error processing image'

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",port=8080)
