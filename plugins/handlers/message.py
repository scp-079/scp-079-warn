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

from pyrogram import Client, Filters

from .. import glovar
from ..functions.etc import code, general_link, receive_data, thread, user_mention
from ..functions.file import save
from ..functions.filters import exchange_channel, new_group
from ..functions.group import leave_group
from ..functions.ids import init_group_id
from ..functions.telegram import get_admins, get_group_info, leave_chat, send_message
from ..functions.user import report_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.channel & exchange_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def auto_report(client, message):
    try:
        data = receive_data(message)
        if data and "WARN" in data["receivers"]:
            if (data["sender"] == "NOSPAM"
                    and data["action"] == "help" and data["type"] == "report"):
                gid = data["data"]["group_id"]
                init_group_id(gid)
                if glovar.configs[gid]["report"]["auto"]:
                    uid = data["data"]["user_id"]
                    mid = data["data"]["message_id"]
                    text, markup = report_user(gid, uid, 0, mid)
                    thread(send_message, (client, gid, text, mid, markup))
    except Exception as e:
        logger.warning(f"Auto report error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & Filters.new_chat_members & new_group
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def init_group(client, message):
    try:
        gid = message.chat.id
        invited_by = message.from_user.id
        group_name, group_link = get_group_info(client, message.chat)
        text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                f"群组名称：{general_link(group_name, group_link)}\n"
                f"群组 ID：{code(gid)}\n")
        if invited_by == glovar.user_id:
            init_group_id(gid)
            admin_members = get_admins(client, gid)
            if admin_members:
                glovar.admin_ids[gid] = {admin.user.id for admin in admin_members if not admin.user.is_bot}
                save("admin_ids")
                text += f"状态：{code('已加入群组')}"
            else:
                thread(leave_group, (client, gid))
                text += (f"状态：{code('已退出群组')}\n"
                         f"原因：{code('获取管理员列表失败')}")
        else:
            thread(leave_chat, (client, gid))
            text += (f"状态：{code('已退出群组')}\n"
                     f"原因：{code('未授权使用')}\n"
                     f"邀请人：{user_mention(invited_by)}")

        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Auto report error: {e}", exc_info=True)
