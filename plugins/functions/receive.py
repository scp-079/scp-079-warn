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
from copy import deepcopy
from json import loads

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from .channel import get_debug_text
from .etc import code, get_text, thread, user_mention
from .file import save
from .group import leave_group
from .ids import init_group_id, init_user_id
from .telegram import send_message, send_report_message
from .user import report_user

# Enable logging
logger = logging.getLogger(__name__)


def receive_config_commit(data: dict) -> bool:
    # Receive config commit
    try:
        gid = data["group_id"]
        config = data["config"]
        glovar.configs[gid] = config
        save("configs")

        return True
    except Exception as e:
        logger.warning(f"Receive config commit error: {e}", exc_info=True)

    return False


def receive_config_reply(client: Client, data: dict) -> bool:
    # Receive config reply
    try:
        gid = data["group_id"]
        uid = data["user_id"]
        link = data["config_link"]
        text = (f"管理员：{user_mention(uid)}\n"
                f"操作：{code('更改设置')}\n"
                f"说明：{code('请点击下方按钮进行设置')}")
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="前往设置",
                        url=link
                    )
                ]
            ]
        )
        thread(send_report_message, (180, client, gid, text, None, markup))

        return True
    except Exception as e:
        logger.warning(f"Receive config reply error: {e}", exc_info=True)

    return False


def receive_help_report(client: Client, data: dict) -> bool:
    # Receive help report requests
    try:
        gid = data["group_id"]
        if init_group_id(gid):
            if glovar.configs[gid]["report"]["auto"]:
                uid = data["user_id"]
                mid = data["message_id"]
                init_user_id(0)
                text, markup = report_user(gid, uid, 0, mid)
                thread(send_message, (client, gid, text, mid, markup))

        return True
    except Exception as e:
        logger.warning(f"Receive help report error: {e}", exc_info=True)

    return False


def receive_leave_approve(client: Client, data: dict) -> bool:
    # Receive leave approve
    try:
        admin_id = data["admin_id"]
        the_id = data["group_id"]
        reason = data["reason"]
        if reason == "permissions":
            reason = "权限缺失"
        elif reason == "user":
            reason = "缺失 USER"

        if glovar.admin_ids.get(the_id, {}):
            text = get_debug_text(client, the_id)
            text += (f"项目管理员：{user_mention(admin_id)}\n"
                     f"状态：{code('已批准退出该群组')}\n")
            if reason:
                text += f"原因：{code(reason)}\n"

            leave_group(client, the_id)
            thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Receive leave approve error: {e}", exc_info=True)

    return False


def receive_remove_bad(data: dict) -> bool:
    # Receive removed bad users
    try:
        the_id = data["id"]
        the_type = data["type"]
        if the_type == "user":
            if glovar.user_ids.get(the_id):
                glovar.user_ids[the_id] = deepcopy(glovar.default_user_status)

            save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove bad error: {e}", exc_info=True)

    return False


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
