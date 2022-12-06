from chalice.app import Chalice
import os
from chalicelib import file_utils, bot_utils

wit_token = os.environ.get('wit_token')

app = Chalice(app_name='surdobot')

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
        print('Sender is a bot. Skipping...')
        return

    chat = message.get('chat')
    if chat is None:
        return

    chat_id = chat.get('id')
    if chat_id is None:
        return

    if not message.get('voice') and not message.get('video_note'):
        print('Message does not contain voice or video note. Skipping...')
        return

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
        for i in range(3): #attemps
            try:
                print(f'Attempt #{i + 1}...')
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
                reply = bot_utils.append_message(reply, chat_id, message_id, text)
                bot_utils.commit_message(reply)
                return
            except Exception as e:
                print(e)
                pass

    bot_utils.delete_message(reply)
