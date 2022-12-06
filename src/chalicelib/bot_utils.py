import os
import re
from . import string_utils
import telebot
from typing import Union

TELEGRAM_INITIAL_MESSAGE = '- <i>Transcrevendo</i>'
TELEGRAM_PARSE_MODE = 'HTML'

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

    if not message.get('voice') and not message.get('video_note'):
        print('Message does not contain voice or video note. Skipping...')
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

    if chat.get('type') in ['group', 'supergroup', 'channel']:
        if all(bot.get_chat_member(chat.get('id'), user_id).status in ['left', 'kicked'] for user_id in user_ids):
            print('Bot owner is not a member of the group. Skipping...')
            return False
    elif chat.get('type') == 'private':
        if sender.get('id') not in user_ids:
            print('Sender is not the bot owner. Skipping...')
            return False

    return True

def send_initial_message(chat_id: int, message_id: int) -> telebot.types.Message:
    ret = append_message(None, chat_id, message_id, TELEGRAM_INITIAL_MESSAGE)
    ret.initial = True  # type: ignore
    return ret  # type: ignore

def append_message(reply, chat_id: int, message_id: int, text: str) -> Union[telebot.types.Message, bool, None]:
    if reply:
        if reply.initial:
            reply.initial = False
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
        return append_message(None, chat_id, ret.message_id, next)  # type: ignore

    ret.initial = False # type: ignore
    return ret

def commit_message(reply) -> None:
    if reply.initial:
        delete_message(reply)
    else:
        bot.edit_message_text(chat_id = reply.chat.id,
                              message_id = reply.message_id,
                              text = reply.text[:-4],
                              parse_mode = TELEGRAM_PARSE_MODE)

def delete_message(reply) -> None:
    bot.delete_message(reply.chat.id, reply.message_id)
