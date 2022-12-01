from chalice.app import Chalice
import os
import telebot
from typing import Union, Tuple

MAX_DURATION = 300
MAX_SIZE = 20 * 1024 * 1024 #MB

OGG_FILE_NAME = '/tmp/audio.ogg'
WAV_FILE_NAME = '/tmp/audio.wav'
AAC_FILE_NAME = '/tmp/audio.aac'
MP4_FILE_NAME = '/tmp/video.mp4'
OUT_FILE_NAME = '/tmp/out%03d.wav'
OUT_BLOB = '/tmp/out*.wav'

TELEGRAM_PARSE_MODE = 'HTML'
TELEGRAM_INITIAL_MESSAGE = '- Transcrevendo ...'

bot_token = os.environ.get("bot_token")
if bot_token is None:
    print('bot_token is not assigned')
    exit()

wit_token = os.environ.get("wit_token")

app = Chalice(app_name='surdobot')
bot = telebot.TeleBot(bot_token)

def download_file(file_id: str, file_name: str) -> None:
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

def get_file_id(file) -> Union[str, None]:
    file_size = file.get('file_size')
    if file_size <= MAX_SIZE:
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

def split_file(file: str):
    import subprocess
    import glob

    subprocess.Popen(['ffmpeg', '-y', '-i', file, '-f', 'segment', '-segment_time', str(MAX_DURATION), '-c', 'copy', OUT_FILE_NAME]).wait()
    return glob.glob(OUT_BLOB)

def get_files(message) -> Union[list[str], None]:
    voice = message.get('voice')
    file = None
    duration = None
    if voice:
        file = get_voice_file(voice)
        duration = voice.get('duration')

    video = message.get('video_note')
    if video:
        file = get_video_file(video)
        duration = video.get('duration')

    if file:
        if duration and duration <= MAX_DURATION:
            return [file]
        else:
            return split_file(file)

def ellipsis(old: Union[str, None], new: str) -> str:
    if old:
        return f'{old[:-3]}{new} ...'
    else:
        return f'{new} ...'

def split(old: Union[str, None], new: str) -> Tuple[str, Union[str, None]]:
    length = 4096 - 4
    if old:
        length -= len(old) - 3

    if len(new) < length:
        return (ellipsis(old, new), None)

    index = new[:length].rfind(' ')
    return (ellipsis(old, new[:index]), new[index + 1:])

def append_message(reply, chat_id: int, message_id: int, text: str) -> Union[telebot.types.Message, bool, None]:
    if reply:
        if reply.text == TELEGRAM_INITIAL_MESSAGE:
            (cur, next) = split(None, text)
        else:
            (cur, next) = split(reply.text, text)

        ret = bot.edit_message_text(chat_id = reply.chat.id,
                                    message_id = reply.message_id,
                                    text = cur,
                                    parse_mode = TELEGRAM_PARSE_MODE)
    else:
        (cur, next) = split(None, text)
        ret = bot.send_message(chat_id = chat_id,
                               reply_to_message_id = message_id,
                               text = cur,
                               parse_mode = TELEGRAM_PARSE_MODE)

    if next:
        return append_message(None, chat_id, ret.message_id, next)  # type: ignore

    return ret

def commit_message(reply) -> None:
    if reply.text == TELEGRAM_INITIAL_MESSAGE:
        delete_message(reply)
    else:
        bot.edit_message_text(chat_id = reply.chat.id,
                              message_id = reply.message_id,
                              text = reply.text[:-4],
                              parse_mode = TELEGRAM_PARSE_MODE)

def delete_message(reply) -> None:
    bot.delete_message(reply.chat.id, reply.message_id)

@app.route('/webhook', methods=['POST'])
def webhook() -> None:
    import json
    import requests
    import re

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

    if not message.get('voice') and not message.get('video_note'):
        return

    reply = bot.send_message(chat_id = chat_id,
                             reply_to_message_id = message_id,
                             text = TELEGRAM_INITIAL_MESSAGE,
                             parse_mode = TELEGRAM_PARSE_MODE)
    try:
        files = get_files(message)
    except Exception as e:
        print(e)
        delete_message(reply)
        return
    if files is None:
        delete_message(reply)
        return
    for file in files:
        for i in range(3): #attemps
            try:
                print(f'Attempt #{i + 1}...')
                with open(file, 'rb') as f:
                    resp = requests.post(
                        #?v=20221114
                        #&context=%7B%22locale%22%3A%22pt_BR%22%7D
                        'https://api.wit.ai/dictation',
                        headers = {
                            'Content-Type': 'audio/wave',
                            'Authorization': f'Bearer {wit_token}'
                        },
                        data = f,
                        stream = True)

                bytes = resp.raw.read()
                content = bytes.decode(json.detect_encoding(bytes))
                data = re.split(r'(?<=\})\s*(?=\{)', content)
                jsons = [json.loads(item) for item in data]
                finals = [obj.get('text') for obj in jsons if obj.get('is_final')]
                reply = append_message(reply, chat_id, message_id, ' '.join(finals))
                commit_message(reply)
                return
            except Exception as e:
                print(e)
                pass

    delete_message(reply)
