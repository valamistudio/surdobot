from chalice import Chalice
import os
import json
import requests
import telebot
from pydub import AudioSegment

app = Chalice(app_name='surdobot')
bot_token = os.environ.get("bot_token")
wit_token = os.environ.get("wit_token")
bot = telebot.TeleBot(bot_token)

@app.route('/webhook', methods=['POST'])
def webhook():
    request = app.current_request
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

    voice = message.get('voice')
    if voice is None:
        return

    duration = voice.get('duration')
    if duration > 300:
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

    file_id = voice.get('file_id')
    if file_id is None:
        return

    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    ogg_file_name = '/tmp/audio.ogg'
    wav_file_name = '/tmp/audio.wav'
    with open(ogg_file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    AudioSegment.from_ogg(ogg_file_name).export(wav_file_name, format = 'wav')
    with open(wav_file_name, 'rb') as f:
        resp = requests.post(
            #&context=%7B%22locale%22%3A%22pt_BR%22%7D
            'https://api.wit.ai/dictation?v=20221114',
            headers = {
                'Content-Type': 'audio/wave',
                'Authorization': f'Bearer {wit_token}'
            },
            data = f,
            stream = True)

    for chunk in resp.raw.read_chunked():
        obj = json.loads(chunk)
        is_final = obj.get('is_final')
        if is_final:
            text = obj.get('text')
            if text:
                print(f'Transcribed text: "{text}"')
                bot.send_message(chat_id = chat_id,
                    reply_to_message_id = message_id,
                    text = text)
