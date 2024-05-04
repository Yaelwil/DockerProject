import time
from pathlib import Path
from flask import Flask, request
from detect import run
import uuid
import yaml
from loguru import logger
import os
import pymongo
import boto3
from flask import Flask, jsonify

images_bucket = os.environ['BUCKET_NAME']

with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']

app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def predict():
    # Generates a UUID for this current prediction HTTP request. This id can be used as a reference in logs to identify
    # and track individual prediction requests.
    prediction_id = str(uuid.uuid4())

    logger.info(f'prediction: {prediction_id}. start processing')

    # Receives a URL parameter representing the image to download from S3
    img_name = request.args.get('imgName')

    if img_name is None:
        logger.error("Missing 'imgName' parameter in the request")
        return jsonify({"error": "Missing 'imgName' parameter"}), 400

    # Create an S3 client
    s3 = boto3.client('s3')

    # Define the local filename to save the downloaded file
    file_name = img_name.split('/')[-1]
    # Expand the $HOME variable to the user's home directory
    home_dir = os.path.expanduser('~')

    # Define the full path to the file
    original_img_path = os.path.join(home_dir, file_name)
    # Download the file
    s3.download_file(images_bucket, img_name, original_img_path)

    logger.info(f'prediction: {prediction_id}/{original_img_path}. Download img completed')

    # Predicts the objects in the image
    run(
        weights='yolov5s.pt',
        data='data/coco128.yaml',
        source=original_img_path,
        project='static/data',
        name=prediction_id,
        save_txt=True
    )

    logger.info(f'prediction: {prediction_id}{original_img_path}. done')


    predicted_img_path = f'static/data/{prediction_id}/{os.path.basename(original_img_path)}'

    # Combine the base name and the file extension
    base_name, file_extension = os.path.splitext(os.path.basename(original_img_path))
    new_file_name = f"{base_name}-predict{file_extension}"

    # new folder in S3
    s3_predicted_directory_path = 'predicted_photos/'

    # full name in S3
    full_name_s3=s3_predicted_directory_path + new_file_name


    # Upload the predicted image to S3
    s3.upload_file(predicted_img_path, images_bucket, full_name_s3)

    logger.info(f'prediction: {new_file_name}. was upload to s3 successfully')

    # Parse prediction labels and create a summary
    pred_summary_path = Path(f'static/data/{prediction_id}/labels{original_img_path.split(".")[0]}.txt')
    if pred_summary_path.exists():
        with open(pred_summary_path) as f:
            labels = f.read().splitlines()
            labels = [line.split(' ') for line in labels]
            labels = [{
                'class': names[int(l[0])],
                'cx': float(l[1]),
                'cy': float(l[2]),
                'width': float(l[3]),
                'height': float(l[4]),
            } for l in labels]

        logger.info(f'prediction: {prediction_id}/{original_img_path}. prediction summary:\n\n{labels}')

        prediction_summary = {
            'prediction_id': prediction_id,
            'original_img_path': original_img_path,
            'predicted_img_path': predicted_img_path,
            'labels': labels,
            'time': time.time()
        }

        # TODO store the prediction_summary in MongoDB
        # Connect to MongoDB
        client = pymongo.MongoClient("mongodb://mongodb_primary:27017/")
        db = client["docker_project"]
        # Select or create a collection for predictions
        collection = db["predictions"]
        # Insert JSON data into MongoDB
        collection.insert_one(prediction_summary)

        return prediction_summary
    else:
        return f'prediction: {prediction_id}/{original_img_path}. prediction result not found', 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
