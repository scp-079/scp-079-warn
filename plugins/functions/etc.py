# SCP-079-WARN - Warn or ban someone by admin commands
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-WARN.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from json import dumps, loads
from random import choice, uniform
from string import ascii_letters, digits
from threading import Thread, Timer
from time import sleep
from typing import Callable, List, Optional, Union

from pyrogram import InlineKeyboardMarkup, Message, User
from pyrogram.errors import FloodWait

# Enable logging
logger = logging.getLogger(__name__)


def bold(text) -> str:
    # Get a bold text
    try:
        text = str(text)
        if text.strip():
            return f"**{text}**"
    except Exception as e:
        logger.warning(f"Bold error: {e}", exc_info=True)

    return ""


def button_data(action: str, action_type: str = None, data: Union[int, str] = None) -> Optional[bytes]:
    # Get a button's bytes data
    result = None
    try:
        button = {
            "a": action,
            "t": action_type,
            "d": data
        }
        result = dumps(button).replace(" ", "").encode("utf-8")
    except Exception as e:
        logger.warning(f"Button data error: {e}", exc_info=True)

    return result


def code(text) -> str:
    # Get a code text
    try:
        text = str(text)
        if text.strip():
            return f"`{text}`"
    except Exception as e:
        logger.warning(f"Code error: {e}", exc_info=True)

    return ""


def code_block(text) -> str:
    # Get a code block text
    try:
        text = str(text)
        if text.strip():
            return f"```{text}```"
    except Exception as e:
        logger.warning(f"Code block error: {e}", exc_info=True)

    return ""


def delay(secs: int, target: Callable, args: list) -> bool:
    # Call a function with delay
    try:
        t = Timer(secs, target, args)
        t.daemon = True
        t.start()
        return True
    except Exception as e:
        logger.warning(f"Delay error: {e}", exc_info=True)

    return False


def format_data(sender: str, receivers: List[str], action: str, action_type: str, data=None) -> str:
    # See https://scp-079.org/exchange/
    text = ""
    try:
        data = {
            "from": sender,
            "to": receivers,
            "action": action,
            "type": action_type,
            "data": data
        }
        text = code_block(dumps(data, indent=4))
    except Exception as e:
        logger.warning(f"Format data error: {e}", exc_info=True)

    return text


def general_link(text: Union[int, str], link: str) -> str:
    # Get a general markdown link
    result = ""
    try:
        result = f"[{text}]({link})"
    except Exception as e:
        logger.warning(f"General link error: {e}", exc_info=True)

    return result


def get_channel_link(message: Union[int, Message]) -> str:
    # Get a channel reference link
    text = ""
    try:
        text = "https://t.me/"
        if isinstance(message, int):
            text += f"c/{str(message)[4:]}"
        else:
            if message.chat.username:
                text += f"{message.chat.username}"
            else:
                cid = message.chat.id
                text += f"c/{str(cid)[4:]}"
    except Exception as e:
        logger.warning(f"Get channel link error: {e}", exc_info=True)

    return text


def get_callback_data(message: Message) -> List[dict]:
    # Get a message's inline button's callback data
    callback_data_list = []
    try:
        if message.reply_markup and isinstance(message.reply_markup, InlineKeyboardMarkup):
            reply_markup = message.reply_markup
            if reply_markup.inline_keyboard:
                inline_keyboard = reply_markup.inline_keyboard
                if inline_keyboard:
                    for button_row in inline_keyboard:
                        for button in button_row:
                            if button.callback_data:
                                callback_data = button.callback_data
                                callback_data = loads(callback_data)
                                callback_data_list.append(callback_data)
    except Exception as e:
        logger.warning(f"Get callback data error: {e}", exc_info=True)

    return callback_data_list


def get_command_context(message: Message) -> str:
    # Get the context "b" in "/command a b"
    result = ""
    try:
        text = get_text(message)
        command_list = text.split(" ")
        if len(list(filter(None, command_list))) > 2:
            i = 1
            command_type = command_list[i]
            while command_type == "" and i < len(command_list):
                i += 1
                command_type = command_list[i]

            result = text[1 + len(command_list[0]) + i + len(command_type):].strip()
    except Exception as e:
        logger.warning(f"Get command context error: {e}", exc_info=True)

    return result


def get_full_name(user: User) -> str:
    # Get user's full name
    text = ""
    try:
        if user and not user.is_deleted:
            text = user.first_name
            if user.last_name:
                text += f" {user.last_name}"
    except Exception as e:
        logger.warning(f"Get full name error: {e}", exc_info=True)

    return text


def get_reason(message: Message, text: str) -> str:
    # Get the reason text
    try:
        command_list = list(filter(None, get_text(message).split(" ")))
        reason = get_text(message)[len(command_list[0]):].strip()
        if reason:
            text += f"原因：{code(reason)}\n"
    except Exception as e:
        logging.warning(f"Get reason error: {e}", exc_info=True)

    return text


def get_text(message: Message) -> str:
    # Get message's text
    text = ""
    try:
        if message.text or message.caption:
            if message.text:
                text += message.text
            else:
                text += message.caption
    except Exception as e:
        logger.warning(f"Get text error: {e}", exc_info=True)

    return text


def message_link(message: Message) -> str:
    # Get a message link in a channel
    text = ""
    try:
        mid = message.message_id
        text = f"{get_channel_link(message)}/{mid}"
    except Exception as e:
        logger.warning(f"Message link error: {e}", exc_info=True)

    return text


def random_str(i: int) -> str:
    # Get a random string
    text = ""
    try:
        text = "".join(choice(ascii_letters + digits) for _ in range(i))
    except Exception as e:
        logger.warning(f"Random str error: {e}", exc_info=True)

    return text


def receive_data(message: Message) -> dict:
    # Receive data from exchange channel
    data = {}
    try:
        text = get_text(message)
        if text:
            data = loads(text)
    except Exception as e:
        logger.warning(f"Receive data error: {e}")

    return data


def thread(target: Callable, args: tuple) -> bool:
    # Call a function using thread
    try:
        t = Thread(target=target, args=args)
        t.daemon = True
        t.start()
        return True
    except Exception as e:
        logger.warning(f"Thread error: {e}", exc_info=True)

    return False


def user_mention(uid: int) -> str:
    # Get a mention text
    text = ""
    try:
        text = f"[{uid}](tg://user?id={uid})"
    except Exception as e:
        logger.warning(f"User mention error: {e}", exc_info=True)

    return text


def wait_flood(e: FloodWait) -> bool:
    # Wait flood secs
    try:
        sleep(e.x + uniform(0.5, 1.0))
        return True
    except Exception as e:
        logger.warning(f"Wait flood error: {e}", exc_info=True)

    return False
