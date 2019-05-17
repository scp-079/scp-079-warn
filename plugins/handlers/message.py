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

from pyrogram import Client, Filters, InlineKeyboardButton, InlineKeyboardMarkup

from .. import glovar
from ..functions.etc import code, receive_data, thread, user_mention
from ..functions.file import save
from ..functions.filters import exchange_channel, hide_channel, new_group
from ..functions.group import get_debug_text, leave_group
from ..functions.ids import init_group_id, init_user_id
from ..functions.telegram import get_admins, leave_chat, send_message, send_report_message
from ..functions.user import report_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.channel & hide_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def exchange_emergency(_, message):
    try:
        # Read basic information
        data = receive_data(message)
        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]
        if "EMERGENCY" in receivers:
            if sender == "EMERGENCY":
                if action == "backup":
                    if action_type == "hide":
                        glovar.should_hide = data
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & Filters.new_chat_members & new_group)
def init_group(client, message):
    try:
        gid = message.chat.id
        invited_by = message.from_user.id
        text = get_debug_text(client, message.chat)
        # Check permission
        if invited_by == glovar.user_id:
            # Update group's admin list
            if init_group_id(gid):
                admin_members = get_admins(client, gid)
                if admin_members:
                    glovar.admin_ids[gid] = {admin.user.id for admin in admin_members if not admin.user.is_bot}
                    save("admin_ids")
                    text += f"状态：{code('已加入群组')}\n"
                else:
                    thread(leave_group, (client, gid))
                    text += (f"状态：{code('已退出群组')}\n"
                             f"原因：{code('获取管理员列表失败')}\n")
        else:
            thread(leave_chat, (client, gid))
            if gid in glovar.left_group_ids:
                return
            else:
                glovar.left_group_ids.add(gid)

            text += (f"状态：{code('已退出群组')}\n"
                     f"原因：{code('未授权使用')}\n"
                     f"邀请人：{user_mention(invited_by)}\n")

        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Auto report error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.channel & exchange_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def process_data(client, message):
    try:
        data = receive_data(message)
        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]
        # This will look awkward,
        # seems like it can be simplified,
        # but this is to ensure that the permissions are clear,
        # so it is intentionally written like this
        if "WARN" in receivers:
            if sender == "CONFIG":

                if action == "config":
                    if action_type == "commit":
                        gid = data["group_id"]
                        config = data["config"]
                        glovar.configs[gid] = config
                        save("configs")
                    elif action_type == "reply":
                        gid = data["group_id"]
                        uid = data["user_id"]
                        link = data["config_link"]
                        text = (f"管理员：{user_mention(uid)}\n"
                                f"操作：{code('更改设置')}\n"
                                f"说明：{code('请点击下方按钮进行设置')}\n")
                        markup = InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "前往设置",
                                        url=link
                                    )
                                ]
                            ]
                        )
                        thread(send_report_message, (180, client, gid, text, None, markup))

            elif sender == "MANAGE":

                if action == "leave":
                    the_id = data["group_id"]
                    reason = data["reason"]
                    if action_type == "approve":
                        leave_group(client, the_id)
                        text = get_debug_text(client, the_id)
                        text += (f"状态：{code('已退出该群组')}\n"
                                 f"原因：{code(reason)}\n")
                        thread(send_message, (client, glovar.debug_channel_id, text))

                elif action == "remove":
                    the_id = data["id"]
                    the_type = data["type"]
                    if action_type == "bad":
                        if the_type == "user":
                            if glovar.user_ids.get(the_id):
                                glovar.user_ids[the_id] = deepcopy(glovar.default_user_status)

                            save("user_ids")

            elif sender == "NOSPAM":

                if action == "help":
                    if action_type == "report":
                        gid = data["group_id"]
                        if init_group_id(gid):
                            if glovar.configs[gid]["report"]["auto"]:
                                uid = data["user_id"]
                                mid = data["message_id"]
                                init_user_id(0)
                                text, markup = report_user(gid, uid, 0, mid)
                                thread(send_message, (client, gid, text, mid, markup))
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)
