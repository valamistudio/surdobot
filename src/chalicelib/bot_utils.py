from __future__ import annotations
import os
import re
from . import string_utils
import telebot

TELEGRAM_INITIAL_MESSAGE = '- <i>Transcribing</i>'
TELEGRAM_PARSE_MODE = 'HTML'

# Although file_utils has an implementation for splitting long audio files before sending to Wit.AI
# And although the maximum duration is 300 seconds (5 minutes) for Wit.AI
# The bot is not behaving as expected for audios longer than ~75s, so I'm hard capping this for now
MAX_DURATION = 75

__user_ids = os.environ.get('user_ids')
user_ids = [int(user_id) for user_id in filter(None, re.split(r'[,;]', __user_ids))] if __user_ids else None

bot_token = os.environ.get("bot_token")
if bot_token is None:
    print('bot_token is not assigned')
    exit()

bot = telebot.TeleBot(bot_token)

def validate_message(message) -> bool:
    if message is None:
        return False

    voice = message.get('voice')
    if voice is None:
        voice = message.get('video_note')

    if voice is None:
        print('Message does not contain voice or video note. Skipping...')
        return False

    duration = voice.get('duration')
    if duration > MAX_DURATION:
        print(f'Audio is longer than {MAX_DURATION}s ({duration}s). Skipping...')
        return False

    chat = message.get('chat')
    if chat is None:
        print('Chat could not be found. This is unexpected. Skipping...')
        return False

    sender = message.get('from')
    if sender is None:
        sender = message.get('sender_chat')

    if sender is None:
        print('Sender could not be found. This is unexpected. Skipping...')
        return False

    if sender.get('is_bot'):
        print('Sender is a bot. Skipping...')
        return False

    # no whitelist set, allow everyone
    if user_ids is None:
        return True

    if chat.get('type') == 'private':
        if sender.get('id') not in user_ids:
            print('Sender is not the bot owner. Skipping...')
            return False
    else: #group, supergroup or channel
        if all(bot.get_chat_member(chat.get('id'), user_id).status in ['left', 'kicked'] for user_id in user_ids):
            print('Bot owner is not a member of the group. Skipping...')
            return False

    return True

def send_initial_message(chat_id: int, message_id: int) -> telebot.types.Message:
    ret = append_message(None, chat_id, message_id, TELEGRAM_INITIAL_MESSAGE)
    ret.initial = True # type: ignore
    return ret

def append_message(reply: telebot.types.Message | None, chat_id: int, message_id: int, text: str) -> telebot.types.Message:
    if reply:
        if reply.initial: # type: ignore
            reply.initial = False # type: ignore
            (cur, next) = string_utils.split(None, text)
        else:
            (cur, next) = string_utils.split(reply.text, text)

        ret = bot.edit_message_text(chat_id = reply.chat.id,
                                    message_id = reply.message_id,
                                    text = cur,
                                    parse_mode = TELEGRAM_PARSE_MODE)
    else:
        (cur, next) = string_utils.split(None, text)
        ret = bot.send_message(chat_id = chat_id,
                               reply_to_message_id = message_id,
                               text = cur,
                               parse_mode = TELEGRAM_PARSE_MODE)

    if next:
        return append_message(None, chat_id, ret.message_id, next) # type: ignore

    ret.initial = False # type: ignore
    return ret # type: ignore

def commit_message(reply: telebot.types.Message) -> None:
    if reply.initial: # type: ignore
        delete_message(reply)
    else:
        bot.edit_message_text(chat_id = reply.chat.id,
                              message_id = reply.message_id,
                              text = reply.text[:-4], # type: ignore
                              parse_mode = TELEGRAM_PARSE_MODE)

def delete_message(reply: telebot.types.Message) -> None:
    bot.delete_message(reply.chat.id, reply.message_id)
