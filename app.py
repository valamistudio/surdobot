from chalice.app import Chalice
import os
import telebot
from typing import Union

MAX_DURATION = 300
MAX_SIZE = 20 * 1024 * 1024 #MB

OGG_FILE_NAME = '/tmp/audio.ogg'
WAV_FILE_NAME = '/tmp/audio.wav'
AAC_FILE_NAME = '/tmp/audio.aac'
MP4_FILE_NAME = '/tmp/video.mp4'

bot_token = os.environ.get("bot_token")
if bot_token is None:
    print('bot_token is not assigned')
    exit()

wit_token = os.environ.get("wit_token")

app = Chalice(app_name='surdobot')
bot = telebot.TeleBot(bot_token)

def download_file(file_id, file_name) -> None:
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

def get_file_id(file) -> Union[str, None]:
    duration = file.get('duration')
    file_size = file.get('file_size')
    if duration <= MAX_DURATION and file_size <= MAX_SIZE:
        return file.get('file_id')

def get_voice_file(voice) -> Union[str, None]:
    import subprocess

    file_id = get_file_id(voice)
    if file_id is None:
        return

    download_file(file_id, OGG_FILE_NAME)

    subprocess.Popen(['ffmpeg', '-y', '-i', OGG_FILE_NAME, WAV_FILE_NAME]).wait()

    return WAV_FILE_NAME

def get_video_file(video) -> Union[str, None]:
    import subprocess

    file_id = get_file_id(video)
    if file_id is None:
        return

    download_file(file_id, MP4_FILE_NAME)

    subprocess.Popen(['ffmpeg', '-y', '-i', MP4_FILE_NAME, '-vn', '-acodec', 'copy', AAC_FILE_NAME]).wait()
    subprocess.Popen(['ffmpeg', '-y', '-i', AAC_FILE_NAME, WAV_FILE_NAME]).wait()

    return WAV_FILE_NAME

def get_file(message) -> Union[str, None]:
    voice = message.get('voice')
    if voice:
        return get_voice_file(voice)

    video = message.get('video_note')
    if video:
        return get_video_file(video)

def append_message(reply, chat_id, message_id, text) -> Union[telebot.types.Message, bool, None]:
    if reply:
        return bot.edit_message_text(chat_id = reply.chat.id,
                                     message_id = reply.message_id,
                                     text = f'{reply.text[:-3]}{text} ...')
    else:
        return bot.send_message(chat_id = chat_id,
                                reply_to_message_id = message_id,
                                text = f'{text} ...')

def commit_message(reply) -> None:
    if reply:
        bot.edit_message_text(chat_id = reply.chat.id,
                              message_id = reply.message_id,
                              text = reply.text[:-4])

@app.route('/webhook', methods=['POST'])
def webhook() -> None:
    import json
    import requests

    request = app.current_request
    if request is None:
        return

    body = request.json_body
    if body is None:
        return

    print(body)

    message = body.get('message')
    if message is None:
        return

    message_id = message.get('message_id')
    if message_id is None:
        return

    sender = message.get('from')
    if sender is None:
        return

    is_bot = sender.get('is_bot')
    if is_bot:
        return

    chat = message.get('chat')
    if chat is None:
        return

    chat_id = chat.get('id')
    if chat_id is None:
        return

    file = get_file(message)
    if file is None:
        return

    for _ in range(3): #attemps
        with open(file, 'rb') as f:
            resp = requests.post(
                #&context=%7B%22locale%22%3A%22pt_BR%22%7D
                'https://api.wit.ai/dictation?v=20221114',
                headers = {
                    'Content-Type': 'audio/wave',
                    'Authorization': f'Bearer {wit_token}'
                },
                data = f,
                stream = True)

        transfer_encoding = resp.headers.get('transfer-encoding')
        if transfer_encoding == 'chunked':
            reply = None
            for chunk in resp.raw.read_chunked():
                try:
                    obj = json.loads(chunk)
                except:
                    continue

                is_final = obj.get('is_final')
                if is_final is None:
                    continue

                text = obj.get('text')
                if text:
                    print(f'Transcribed text: "{text}"')
                    reply = append_message(reply, chat_id, message_id, text)

            commit_message(reply)
            break #sucess, no need to retry
        else:
            content = resp.json()
            print(f'Not chunked response: {content}')
            code = content.get('code')
            if code != 'timeout':
                break
