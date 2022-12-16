from __future__ import annotations
import os
from chalice.app import Chalice
import sys
import telebot
from retry import retry
from chalicelib import file_utils, bot_utils

wit_token = os.environ.get('wit_token')
if wit_token is None:
    print('wit_token is not assigned')
    sys.exit()

app = Chalice(app_name='surdobot')

@retry(tries = 3)
def respond(file: str, chat_id, message_id, reply: telebot.types.Message) -> telebot.types.Message | None:
    import json
    import requests
    import re
    with open(file, 'rb') as f:
        resp = requests.post(
            #?v=20221114
            #&context=%7B%22locale%22%3A%22pt_BR%22%7D
            'https://api.wit.ai/dictation',
            headers = {
                'Content-Type': file_utils.CONTENT_TYPE,
                'Authorization': f'Bearer {wit_token}'
            },
            data = f,
            stream = True)

    bytes = resp.raw.read()
    content = bytes.decode(json.detect_encoding(bytes))
    data = re.split(r'(?<=\})\s*(?=\{)', content)
    jsons = [json.loads(item) for item in data]
    finals = [obj.get('text') for obj in jsons if obj.get('is_final')]
    text = ' '.join(finals)
    print(f'Transcribed text: {text}')
    return bot_utils.append_message(reply, chat_id, message_id, text)

@app.route('/webhook', methods=['POST'])
def webhook() -> None:
    request = app.current_request
    if request is None:
        return

    body = request.json_body
    if body is None:
        return

    print(body)

    message = body.get('message')
    if message is None:
        message = body.get('channel_post')

    if not bot_utils.validate_message(message):
        return

    message_id = message.get('message_id')
    chat = message.get('chat')
    chat_id = chat.get('id')
    reply = bot_utils.send_initial_message(chat_id, message_id)

    try:
        files = file_utils.get_files(message)
    except Exception as e:
        print(e)
        bot_utils.delete_message(reply)
        return

    if files is None:
        bot_utils.delete_message(reply)
        return

    for file in files:
        new_reply = respond(file, chat_id, message_id, reply)
        if new_reply:
            reply = new_reply
        else:
            bot_utils.delete_message(reply)
            return

    bot_utils.commit_message(reply)
