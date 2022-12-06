import os
from . import string_utils
import telebot
from typing import Union

TELEGRAM_INITIAL_MESSAGE = '- <i>Transcrevendo</i>'
TELEGRAM_PARSE_MODE = 'HTML'

bot_token = os.environ.get("bot_token")
if bot_token is None:
    print('bot_token is not assigned')
    exit()

bot = telebot.TeleBot(bot_token)

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
