import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
import random

#from polybot.img_proc import Img
#from polybot.responses import load_responses
from img_proc import Img
from responses import load_responses


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
        else:
            # If no greeting or well-being question, respond with the original message
            default_response = random.choice(self.responses['default'])
            self.send_text(msg['chat']['id'], default_response)


class ObjectDetectionBot(Bot):

    def __init__(self, token, telegram_chat_url):
        super().__init__(token, telegram_chat_url)
        self.responses = load_responses()

    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if self.is_current_msg_photo(msg):
            photo_path = self.download_user_photo(msg)

            # TODO upload the photo to S3
            # TODO send an HTTP request to the `yolo5` service for prediction
            # TODO send the returned results to the Telegram end-user


class ImageProcessingBot(Bot):

    def __init__(self, token, telegram_chat_url):
        super().__init__(token, telegram_chat_url)
        self.responses = load_responses()

    def handle_message(self, msg):
        logger.info(f'Message: {msg}')

        # Check if the message contains a photo with a caption
        if 'photo' in msg:
            if 'caption' in msg:

                photo_caption = msg['caption'].lower()

                try:
                    # Check for specific keywords in the caption to determine the filter to apply
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