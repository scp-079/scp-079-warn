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
from time import sleep
from typing import List, Optional, Union

from pyrogram import Chat, Client, Message
from pyrogram.errors import FloodWait

from .. import glovar
from .etc import code, code_block, general_link, get_full_name, get_command_type, get_text, message_link, thread
from .file import crypt_file, delete_file, get_new_path, save
from .telegram import get_group_info, send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def ask_for_help(client: Client, level: str, gid: int, uid: int, group: str = "single") -> bool:
    # Let USER help to delete all message from user, or ban user globally
    try:
        data = {
                "group_id": gid,
                "user_id": uid
        }
        if level == "delete":
            data["type"] = group

        share_data(
            client=client,
            receivers=["USER"],
            action="help",
            action_type=level,
            data=data
        )
        return True
    except Exception as e:
        logger.warning(f"Ask for help error: {e}", exc_info=True)

    return False


def exchange_to_hide(client: Client) -> bool:
    # Let other bots exchange data in the hide channel instead
    try:
        glovar.should_hide = True
        text = format_data(
            sender="EMERGENCY",
            receivers=["EMERGENCY"],
            action="backup",
            action_type="hide",
            data=True
        )
        thread(send_message, (client, glovar.hide_channel_id, text))
        return True
    except Exception as e:
        logger.warning(f"Exchange to hide error: {e}", exc_info=True)

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


def forward_evidence(client: Client, message: Message, level: str, rule: str) -> Optional[Union[bool, Message]]:
    # Forward the message to logging channel as evidence
    result = None
    try:
        if not message or not message.from_user:
            return result

        uid = message.from_user.id
        text = (f"项目编号：{code(glovar.sender)}\n"
                f"用户 ID：{code(uid)}\n"
                f"操作等级：{code(level)}\n"
                f"规则：{code(rule)}\n")
        if message.from_user.is_self:
            if message.from_user.is_self is True:
                if message.entities:
                    for en in message.entities:
                        if en.user:
                            name = get_full_name(en.user)
                            if name:
                                text += f"用户昵称：{code(name)}\n"
                                break

                text += f"附加信息：{code('群管直接回复汇报消息')}\n"
            # User didn't use report function wisely, should not forward evidence
            else:
                text += f"附加信息：{code(message.from_user.is_self)}"

            result = send_message(client, glovar.logging_channel_id, text)
        else:
            name = get_full_name(message.from_user)
            if name:
                text += f"用户昵称：{code(name)}\n"

            if message.service:
                text += f"附加信息：{code('入群消息')}\n"
                result = send_message(client, glovar.logging_channel_id, text)
            else:
                flood_wait = True
                while flood_wait:
                    flood_wait = False
                    try:
                        result = message.forward(glovar.logging_channel_id)
                    except FloodWait as e:
                        flood_wait = True
                        sleep(e.x + 1)
                    except Exception as e:
                        logger.info(f"Forward evidence message error: {e}", exc_info=True)
                        return False

                result = result.message_id
                result = send_message(client, glovar.logging_channel_id, text, result)
    except Exception as e:
        logger.warning(f"Forward evidence error: {e}", exc_info=True)

    return result


def get_debug_text(client: Client, context: Union[int, Chat]) -> str:
    # Get a debug message text prefix, accept int or Chat
    text = ""
    try:
        if isinstance(context, int):
            group_id = context
        else:
            group_id = context.id

        group_name, group_link = get_group_info(client, context)
        text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                f"群组名称：{general_link(group_name, group_link)}\n"
                f"群组 ID：{code(group_id)}\n")
    except Exception as e:
        logger.warning(f"Get debug text error: {e}", exc_info=True)

    return text


def receive_text_data(message: Message) -> dict:
    # Receive text's data from exchange channel
    data = {}
    try:
        text = get_text(message)
        if text:
            data = loads(text)
    except Exception as e:
        logger.warning(f"Receive data error: {e}")

    return data


def send_debug(client: Client, message: Message, action: str, uid: int, aid: int, em: Message) -> bool:
    # Send the debug message
    try:
        text = get_debug_text(client, message.chat)
        text += (f"用户 ID：{code(uid)}\n"
                 f"执行操作：{code(f'{action}用户')}\n"
                 f"群管理：{code(aid)}\n"
                 f"消息存放：{general_link(em.message_id, message_link(em))}\n")
        # If the message is a report callback message
        if message.from_user.is_self:
            text += f"原因：{code('由群管处理的举报')}\n"
        else:
            reason = get_command_type(message)
            if reason:
                text += f"原因：{code(reason)}\n"

        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Send debug error: {e}", exc_info=True)

    return False


def share_data(client: Client, receivers: List[str], action: str, action_type: str, data: Union[dict, int, str],
               file: str = None, encrypt: bool = True) -> bool:
    # Use this function to share data in the exchange channel
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if glovar.should_hide:
            channel_id = glovar.hide_channel_id
        else:
            channel_id = glovar.exchange_channel_id

        if file:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            if encrypt:
                # Encrypt the file, save to the tmp directory
                file_path = get_new_path()
                crypt_file("encrypt", file, file_path)
            else:
                # Send directly
                file_path = file

            result = send_document(client, channel_id, file_path, text)
            # Delete the tmp file
            if result and "tmp/" in file_path:
                thread(delete_file, (file_path,))
        else:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            result = send_message(client, channel_id, text)

        # Sending failed due to channel issue
        if result is False:
            # Use hide channel instead
            exchange_to_hide(client)
            thread(share_data, (client, receivers, action, action_type, data, file))

        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False


def update_score(client: Client, uid: int) -> bool:
    # Update a user's score, share it
    try:
        ban_count = len(glovar.user_ids[uid]["ban"])
        warn_count = len(glovar.user_ids[uid]["warn"])
        score = ban_count * 1 + warn_count * 0.4
        glovar.user_ids[uid]["score"] = score
        save("user_ids")
        share_data(
            client=client,
            receivers=glovar.receivers_status,
            action="update",
            action_type="score",
            data={
                "id": uid,
                "score": score
            }
        )
        return True
    except Exception as e:
        logger.warning(f"Update score error: {e}", exc_info=True)

    return False
