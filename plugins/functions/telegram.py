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
from time import sleep
from typing import Iterable, List, Optional, Union

from pyrogram import Chat, ChatMember, Client, InlineKeyboardMarkup, Message, ParseMode, User
from pyrogram.errors import ChannelInvalid, ChannelPrivate, FloodWait, PeerIdInvalid

from .. import glovar
from .etc import delay

logger = logging.getLogger(__name__)


def answer_callback(client: Client, query_id: str, text: str) -> Optional[bool]:
    result = None
    try:
        while not result:
            try:
                result = client.answer_callback_query(
                    callback_query_id=query_id,
                    text=text
                )
            except FloodWait as e:
                sleep(e.x + 1)
    except Exception as e:
        logger.warning(f"Answer query to {query_id} error: {e}", exc_info=True)

    return result


def edit_message_text(client: Client, cid: int, mid: int, text: str,
                      markup: InlineKeyboardMarkup = None) -> Optional[Message]:
    result = None
    try:
        if text.strip():
            while not result:
                try:
                    result = client.edit_message_text(
                        chat_id=cid,
                        message_id=mid,
                        text=text,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                        reply_markup=markup
                    )
                except FloodWait as e:
                    sleep(e.x + 1)
    except Exception as e:
        logger.warning(f"Edit message in {cid} error: {e}", exc_info=True)

    return result


def delete_messages(client: Client, cid: int, mids: Iterable[int]) -> Optional[bool]:
    result = None
    try:
        while not result:
            try:
                result = client.delete_messages(chat_id=cid, message_ids=mids)
            except FloodWait as e:
                sleep(e.x + 1)
    except Exception as e:
        logger.warning(f"Delete messages in {cid} error: {e}", exc_info=True)

    return result


def get_admins(client: Client, cid: int) -> Optional[List[ChatMember]]:
    result = None
    try:
        while not result:
            try:
                result = client.get_chat_members(chat_id=cid, filter="administrators")
            except FloodWait as e:
                sleep(e.x + 1)
            except (PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                return None

        result = result.chat_members
    except Exception as e:
        logger.warning(f"Get admin ids in {cid} error: {e}", exc_info=True)

    return result


def get_group_info(client: Client, chat: Union[int, Chat]) -> (str, str):
    group_name = "Unknown Group"
    group_link = glovar.default_group_link
    try:
        if isinstance(chat, int):
            result = None
            while not result:
                try:
                    result = client.get_chat(chat_id=chat)
                except FloodWait as e:
                    sleep(e.x + 1)
                except Exception as e:
                    logger.warning(f"Get chat {chat} error: {e}")

            chat = result

        if chat.title:
            group_name = chat.title

        if chat.username:
            group_link = "https://t.me/" + chat.username
    except Exception as e:
        logger.info('Get group info error: %s', e)

    return group_name, group_link


def get_users(client: Client, uids: Iterable[int]) -> Optional[List[User]]:
    result = None
    try:
        while not result:
            try:
                result = client.get_users(user_ids=uids)
            except FloodWait as e:
                sleep(e.x + 1)
    except Exception as e:
        logger.warning(f"Get users {uids} error: {e}", exc_info=True)

    return result


def kick_chat_member(client: Client, cid: int, uid: int) -> Optional[Union[bool, Message]]:
    result = None
    try:
        while not result:
            try:
                result = client.kick_chat_member(chat_id=cid, user_id=uid)
            except FloodWait as e:
                sleep(e.x + 1)
    except Exception as e:
        logger.warning(f"Kick chat member {uid} in {cid} error: {e}", exc_info=True)

    return result


def leave_chat(client: Client, cid: int) -> bool:
    result = None
    try:
        while not result:
            try:
                result = client.leave_chat(chat_id=cid)
            except FloodWait as e:
                sleep(e.x + 1)

        return True
    except Exception as e:
        logger.warning(f"Leave chat {cid} error: {e}")

    return False


def send_document(client: Client, cid: int, file: str, text: str = None, mid: int = None,
                  markup: InlineKeyboardMarkup = None) -> Optional[Message]:
    result = None
    try:
        while not result:
            try:
                result = client.send_document(
                    chat_id=cid,
                    document=file,
                    caption=text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_to_message_id=mid,
                    reply_markup=markup
                )
            except FloodWait as e:
                sleep(e.x + 1)
    except Exception as e:
        logger.warning(f"Send document to {cid} error: {e}", exec_info=True)

    return result


def send_message(client: Client, cid: int, text: str, mid: int = None,
                 markup: InlineKeyboardMarkup = None) -> Optional[Message]:
    result = None
    try:
        if text.strip():
            while not result:
                try:
                    result = client.send_message(
                        chat_id=cid,
                        text=text,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                        reply_to_message_id=mid,
                        reply_markup=markup
                    )
                except FloodWait as e:
                    sleep(e.x + 1)
    except Exception as e:
        logger.warning(f"Send message to {cid} error: {e}", exc_info=True)

    return result


def send_report_message(secs: int, client: Client, cid: int, text: str, mid: int = None,
                        markup: InlineKeyboardMarkup = None) -> Optional[Message]:
    result = None
    try:
        if text.strip():
            while not result:
                try:
                    result = client.send_message(
                        chat_id=cid,
                        text=text,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                        reply_to_message_id=mid,
                        reply_markup=markup
                    )
                except FloodWait as e:
                    sleep(e.x + 1)

            mid = result.message_id
            mids = [mid]
            delay(secs, delete_messages, [client, cid, mids])
    except Exception as e:
        logger.warning(f"Send message to {cid} error: {e}", exc_info=True)

    return result


def unban_chat_member(client: Client, cid: int, uid: int) -> Optional[bool]:
    result = None
    try:
        while not result:
            try:
                result = client.unban_chat_member(chat_id=cid, user_id=uid)
            except FloodWait as e:
                sleep(e.x + 1)
    except Exception as e:
        logger.warning(f"Unban chat member {uid} in {cid} error: {e}")

    return result
