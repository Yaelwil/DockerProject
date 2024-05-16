import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
import random
import subprocess
import sys
from datetime import datetime
import boto3
import requests
import json

#from polybot.img_proc import Img
#from polybot.responses import load_responses
from img_proc import Img
from responses import load_responses

BOT_TOKEN = os.environ['TELEGRAM_TOKEN']



class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')
        # Load responses from the JSON file
        self.responses = load_responses()

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""

        logger.info(f'Incoming message: {msg}')

        # Check if the user's message contains a greeting
        if 'text' in msg and any(word.lower() in ['hi', 'hello'] for word in msg['text'].split()):
            greeting_response = random.choice(self.responses['greetings'])
            self.send_text(msg['chat']['id'], greeting_response)
        elif 'text' in msg and any(word in msg['text'].lower() for word in ['how are you', 'how you doing']):
            well_being_response = random.choice(self.responses['well_being'])
            self.send_text(msg['chat']['id'], well_being_response)
        elif 'text' in msg and any(word in msg['text'].lower() for word in ['thank']):
            thanks_response = random.choice(self.responses['thanks'])
            self.send_text(msg['chat']['id'], thanks_response)
        elif 'text' in msg and any(word in msg['text'].lower() for word in ['filter', 'which filters']):
            filter_response_intro = random.choice(self.responses['filter']['intro'])
            filter_response_options = "\n".join(self.responses['filter']['options'])
            full_filter_response = f"{filter_response_intro}\n\nAvailable Filters:\n{filter_response_options}"
            self.send_text(msg['chat']['id'], full_filter_response)
        elif 'text' in msg and any(word in msg['text'].lower() for word in ['help']):
            help_response = '\n'.join(self.responses['help'])
            self.send_text(msg['chat']['id'], help_response)
        elif 'text' in msg and 'what is' in msg['text'].lower() and any(word in msg['text'].lower() for word in
                                                                        ['blur', 'contour', 'rotate', 'salt and pepper',
                                                                         'segment', 'random colors', 'predict']):
            # Extract the filter mentioned in the message
            mentioned_filter = next((word for word in
                                     ['blur', 'contour', 'rotate', 'salt and pepper', 'segment', 'random colors',
                                      'predict'] if word in msg['text'].lower()), None)
            if mentioned_filter:
                # Provide relevant information based on the mentioned filter
                if mentioned_filter == 'blur':
                    self.send_text(msg['chat']['id'], self.responses['blur_info'])
                elif mentioned_filter == 'contour':
                    self.send_text(msg['chat']['id'], self.responses['contour_info'])
                elif mentioned_filter == 'rotate':
                    self.send_text(msg['chat']['id'], self.responses['rotate_info'])
                elif mentioned_filter == 'salt_and_pepper':
                    self.send_text(msg['chat']['id'], self.responses['salt and pepper_info'])
                elif mentioned_filter == 'segment':
                    self.send_text(msg['chat']['id'], self.responses['segment_info'])
                elif mentioned_filter == 'random colors':
                    self.send_text(msg['chat']['id'], self.responses['random_colors_info'])
                elif mentioned_filter == 'predict':
                    self.send_text(msg['chat']['id'], self.responses['predict_info'])

        elif 'text' in msg and any(word in msg['text'].lower() for word in ['blur', 'contour', 'rotate', 'salt and pepper', 'segment', 'random color', 'predict']):
            self.send_text(msg['chat']['id'], "Don't forget to send photo")
        else:
            # If no greeting or well-being question, respond with the original message
            default_response = random.choice(self.responses['default'])
            self.send_text(msg['chat']['id'], default_response)


class ObjectDetectionBot(Bot):

    def __init__(self, token, telegram_chat_url):
        super().__init__(token, telegram_chat_url)
        self.responses = load_responses()
        self.s3 = boto3.client('s3')

    def rename_photo_with_timestamp(self, photo_path):
        """
        Rename a photo with a timestamp in the format 'yyyy-mm-dd HH:MM:SS'.
        If multiple photos are saved within the same minute, append a counter
        to the filename.

        Parameters:
            photo_path (str): The path to the photo file locally.

        Returns:
            new_photo_path (str): The new path to the photo file locally.
            new_file_name (str): The new file name locally.
        """

        try:
            # Get current date and time
            current_time = datetime.now()

            # Format the datetime as required
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

            # Get the file extension
            file_name, file_extension = os.path.splitext(photo_path)

            # Check if there's already a photo saved in the same minute
            same_minute_files = [f for f in os.listdir(os.path.dirname(photo_path)) if f.startswith(formatted_time)]

            # Construct the new file name
            if same_minute_files:
                # Append a counter to the file name
                counter = len(same_minute_files) + 1
                new_file_name = f"{formatted_time} p{counter}{file_extension}"
            else:
                new_file_name = f"{formatted_time}{file_extension}"

            # Rename the file
            new_photo_path = os.path.join(os.path.dirname(photo_path), new_file_name.lstrip("/"))
            os.rename(photo_path, new_photo_path)

            return new_photo_path, new_file_name

        except Exception as e:
            logger.error(f"Error renaming photo: {e}")
            raise

    def ensure_s3_directory_exists(self, bucket, directory):
        """
        Makes sure that the specified directory exists in S3. If not, it creates the folder.

        Parameters:
            bucket (str): Bucket name.
            directory (str): Directory to check.
        """

        try:
            # Check if the directory exists by listing objects in the directory
            self.s3.head_object(Bucket=bucket, Key=(directory + '/'))
        except self.s3.exceptions.ClientError as e:
            # If the directory doesn't exist, create it
            if e.response['Error']['Code'] == '404':
                self.s3.put_object(Bucket=bucket, Key=(directory + '/'))
            else:
                raise  # Raise the exception if it's not a '404 Not Found' error

    def upload_photo_to_s3(self, photo_path):
        """
        Upload the photo to S3 bucket.

        Parameters:
            photo_path (str): The path to the photo file locally.

        Returns:
            s3_key (str): The new path to the photo file in S3.
        """

        try:
            # Specify the directory path in the bucket
            s3_directory_path = 'photos'
            s3_predicted_directory_path = 'predicted_photos'
            s3_json_folder = 'json'

            # Ensure the directory exists in the S3 bucket
            self.ensure_s3_directory_exists('yaelwil-dockerproject', s3_directory_path)
            self.ensure_s3_directory_exists('yaelwil-dockerproject', s3_predicted_directory_path)
            self.ensure_s3_directory_exists('yaelwil-dockerproject', s3_json_folder)

            # Extract filename from the path
            filename = os.path.basename(photo_path)

            # Combine directory path and filename to form the S3 key
            s3_key = s3_directory_path + '/' + filename

            # Upload the photo to S3
            self.s3.upload_file(photo_path, 'yaelwil-dockerproject', s3_key)

            # Return the S3 key
            return s3_key
        except Exception as e:
            logger.error(f"Error uploading photo to S3: {e}")
            return None

    def process_prediction_results(self, json_file_path):
        """
        Process the response from YOLO to the format required in the project.

        Parameters:
            json_file_path (str): Path to the JSON file containing prediction results.

        Returns:
            processed_results (list): Processed prediction to the format required in the project.
        """

        try:
            # Load the prediction results from the JSON file
            with open(json_file_path, "r") as json_file:
                prediction_results = json.load(json_file)

            # Assuming prediction_results is a JSON object
            # Extract relevant information
            labels = prediction_results.get('labels', [])

            # Count occurrences of each object
            object_count = {}
            for label_info in labels:
                label = label_info['class']
                if label in object_count:
                    object_count[label] += 1
                else:
                    object_count[label] = 1

            # Format the results as a list of dictionaries
            processed_results = [{'class': label, 'count': count} for label, count in object_count.items()]

            return processed_results

        except FileNotFoundError as e:
            logger.error(f"Error: Prediction results file not found: {e}")
            return None
        except KeyError as e:
            logger.error(f"Error parsing prediction results: {e}")
            return None

    def call_yolo_service(self, new_photo_path, chat_id):
        """
        Sends an HTTPS request to YOLO to make a prediction of the photo.

        Parameters:
            new_photo_path (str): The new path to the photo file locally, from "rename_photo_with_timestamp" method.
            chat_id (int): Chat ID obtained from the incoming message.
        """

        try:
            # Specify the URL of the YOLOv5 service for prediction
            yolo5_base_url = "http://yolo_app:8081/predict"

            # URL for prediction with the new_photo_path parameter
            yolo5_url = f"{yolo5_base_url}?imgName={new_photo_path}"

            yolo5_url_corrected = yolo5_url

            # Replace "//root" with "/root" only at the beginning of the query string parameter "imgName"
            if yolo5_url.startswith("//root/"):
                yolo5_url_corrected = yolo5_url.replace("//root/", "/root/")

            logger.info(f'yolo5_url_correct: {yolo5_url_corrected}')

            response = requests.post(yolo5_url_corrected)

            logger.info(f'response')

            if response.status_code == 200:
                # Process the prediction results returned by the service
                prediction_results = response.json()

                # Save the prediction results to a JSON file
                json_file_path = "prediction_summary.json"  # Remove last four characters from new_photo_path
                with open(json_file_path, 'w') as json_file:
                    json.dump(prediction_results, json_file)

                logger.info(f"Prediction results saved to {json_file_path}")

                processed_results = self.process_prediction_results(json_file_path)

                return processed_results
            elif response.status_code == 404:

                self.send_text(chat_id, "Error processing the photo")

            else:
                logger.error(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error calling YOLOv5 service: {e}")

    def send_prediction_results_to_telegram(self, processed_results):
        """
        Sends the prediction message to the Telegram user.

        Parameters:
            processed_results (JSON): Processed prediction to the format required in the project.
        """

        try:
            if processed_results:
                # Convert the processed results to a list of strings
                formatted_results = []
                for result in processed_results:
                    if 'class' in result:  # Ensure keys are present
                        formatted_result = f"Object: {result['class']} Count: {result['count']}"
                        formatted_results.append(formatted_result)
                    else:
                        logger.error("Invalid format of processed results.")
                        return  # Exit function if the format is invalid

                # Join the formatted results into a single string
                processed_results_message = "Prediction results:\n" + "\n".join(formatted_results)

                # Send the message to the Telegram end-user using the obtained chat ID
                return processed_results_message
            else:
                logger.error("Error processing prediction results.")
        except Exception as e:
            logger.error(f"Error sending prediction results to Telegram: {e}")

    def send_telegram_message(self, chat_id, message):
        """
        Sends a message to the Telegram user.

        Parameters:
            message (str): The message to be sent.
        """

        try:
            # TODO get the telegram app URL from the enviournment variables
            # Send the message to the Telegram end-user using the obtained chat ID
            telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message
            }
            response = requests.post(telegram_api_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Error sending message to Telegram: {response.text}")
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")

    def apply_filter(self, msg, filter_func, filter_name):
        # Download the photo and apply the specified filter
        img_path = self.download_user_photo(msg)
        img_instance = Img(img_path)
        filter_func(img_instance)  # Call the provided filter function
        processed_img_path = img_instance.save_img()

        # Send the processed image to the user
        self.send_photo(msg['chat']['id'], processed_img_path)
        self.send_text(msg['chat']['id'], f'{filter_name} filter applied successfully.')

    def apply_blur_filter(self, msg):
        self.apply_filter(msg, Img.blur, 'Blur')

    def apply_contour_filter(self, msg):
        self.apply_filter(msg, Img.contour, 'Contour')

    def apply_rotate_filter(self, msg):
        self.apply_filter(msg, Img.rotate, 'Rotate')

    def apply_salt_n_pepper_filter(self, msg):
        self.apply_filter(msg, Img.salt_n_pepper, 'Salt and Pepper')

    def apply_segment_filter(self, msg):
        self.apply_filter(msg, Img.segment, 'Segment')

    def apply_random_colors_filter(self, msg):
        img_path = self.download_user_photo(msg)
        img_instance = Img(img_path)

        # Apply the 'random colors' filter
        img_instance.random_colors()

        processed_img_path = img_instance.save_img()

        # Send the processed image to the user
        self.send_photo(msg['chat']['id'], processed_img_path)
        self.send_text(msg['chat']['id'], 'Random colors filter applied successfully.')

    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        # Check if the message contains a photo with a caption
        if 'photo' in msg:
            if 'caption' in msg:
                photo_caption = msg['caption'].lower()

                try:
                    # Check for specific keywords in the caption to determine the filter to apply
                    if ('blur' in photo_caption or
                            'contour' in photo_caption or
                            'rotate' in photo_caption or
                            'salt and pepper' in photo_caption or
                            'segment' in photo_caption or
                            'random color' in photo_caption):
                        self.image_processing(msg)
                    elif 'predict' in photo_caption:
                        self.object_detection(msg)
                    else:
                        # If no specific filter is mentioned, respond with a default message
                        default_response = random.choice(self.responses['default'])
                        self.send_text(msg['chat']['id'], default_response)

                except Exception:
                    no_permission_response = random.choice(self.responses['photo_errors']['permissions_error'])
                    self.send_text(msg['chat']['id'], no_permission_response)
            else:
                # If photo is sent without a caption, return a random response from the JSON file
                no_captions_response = random.choice(self.responses['photo_errors']['no_caption'])
                self.send_text(msg['chat']['id'], no_captions_response)

                # If the message doesn't contain a photo with a caption, handle it as a regular text message
        else:
            super().handle_message(msg)

    def image_processing(self, msg):
        photo_caption = msg['caption'].lower()

        if 'blur' in photo_caption:
            self.apply_blur_filter(msg)
        elif 'contour' in photo_caption:
            self.apply_contour_filter(msg)
        elif 'rotate' in photo_caption:
            self.apply_rotate_filter(msg)
        elif 'salt and pepper' in photo_caption:
            self.apply_salt_n_pepper_filter(msg)
        elif 'segment' in photo_caption:
            self.apply_segment_filter(msg)
        elif 'random color' in photo_caption:
            self.apply_random_colors_filter(msg)
        else:
            pass

    def object_detection(self, msg):
        if self.is_current_msg_photo(msg):
            photo_path = self.download_user_photo(msg)

            # Rename the photo with timestamp
            new_photo_path, new_file_name = self.rename_photo_with_timestamp(photo_path)

            if new_photo_path and new_file_name:
                # Upload the photo to S3
                s3_key = self.upload_photo_to_s3(new_photo_path)

                # Obtain the chat ID from the incoming message
                chat_id = msg['chat']['id']

                if s3_key:
                    # Call the YOLOv5 service

                    processed_results = self.call_yolo_service(new_photo_path, chat_id)

                    # Send the prediction results to Telegram user
                    processed_results_message = self.send_prediction_results_to_telegram(processed_results)

                    # Check if the processed results message exist
                    if processed_results_message:
                        # Send the processed results message to the Telegram user
                        self.send_telegram_message(chat_id, processed_results_message)
                    else:
                        logger.error("Error sending prediction results message.")
                else:
                    logger.error("Error uploading photo to S3.")
            else:
                logger.error("Error renaming photo.")