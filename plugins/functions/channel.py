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
from typing import List, Optional, Union

from pyrogram import Client, Message
from pyrogram.errors import FloodWait

from .. import glovar
from .etc import code, format_data, general_link, get_reason, thread, user_mention
from .file import crypt_file
from .group import get_debug_text
from .telegram import send_document, send_message


# Enable logging
logger = logging.getLogger(__name__)


def ask_for_help(client: Client, level: str, gid: int, uid: int) -> bool:
    # Let USER help to delete all message from user, or ban user globally
    try:
        share_data(
            client=client,
            receivers=["USER"],
            action="help",
            action_type=level,
            data={
                "group_id": gid,
                "user_id": uid
            }
        )
        return True
    except Exception as e:
        logger.warning(f"Ask for help error: {e}", exc_info=True)

    return False


def forward_evidence(client: Client, message: Message, level: str, rule: str,
                     more: str = None) -> Optional[Union[bool, int]]:
    # Forward the message to logging channel as evidence
    result = None
    try:
        uid = message.from_user.id
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
        text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                f"用户 ID：{code(uid)}\n"
                f"操作等级：{code(level)}\n"
                f"规则：{code(rule)}\n")
        if more:
            text += f"附加信息：{code(more)}\n"

        thread(send_message, (client, glovar.logging_channel_id, text, result))
    except Exception as e:
        logger.warning(f"Forward evidence error: {e}", exc_info=True)

    return result


def send_debug(client: Client, message: Message, action: str, uid: int, aid: int, eid: int) -> bool:
    # Send the debug message
    try:
        text = get_debug_text(client, message.chat)
        text += (f"已{action}用户：{user_mention(uid)}\n"
                 f"群管理：{user_mention(aid)}\n"
                 f"消息存放：{general_link(eid, f'https://t.me/{glovar.logging_channel_username}/{eid}')}\n")
        # If the message is a report callback message
        if message.from_user.is_self or message.from_user.id == glovar.warn_id:
            text += f"原因：{code('由群管处理的举报')}\n"
        else:
            text = get_reason(message, text)

        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Send debug error: {e}", exc_info=True)

    return False


def share_data(client: Client, receivers: List[str], action: str, action_type: str, data: Union[dict, int, str],
               file: str = None) -> bool:
    # Use this function to share data in exchange channel
    try:
        sender = "WARN"
        if file:
            text = format_data(
                sender=sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            crypt_file("encrypt", f"data/{file}", f"tmp/{file}")
            thread(send_document, (client, glovar.exchange_channel_id, f"tmp/{file}", text))
        else:
            text = format_data(
                sender=sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            thread(send_message, (client, glovar.exchange_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False
