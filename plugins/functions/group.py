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
from typing import Union

from pyrogram import Chat, Client

from .. import glovar
from .etc import code, general_link, thread
from .file import save
from .telegram import delete_messages, get_group_info, leave_chat

# Enable logging
logger = logging.getLogger(__name__)


def delete_message(client: Client, gid: int, mid: int) -> bool:
    # Delete a single message
    try:
        mids = [mid]
        thread(delete_messages, (client, gid, mids))
        return True
    except Exception as e:
        logger.warning(f"Delete message error: {e}", exc_info=True)

    return False


def get_debug_text(client: Client, context: Union[int, Chat]) -> str:
    # Get a debug message text prefix, accept int or Chat
    if isinstance(context, int):
        info_para = context
        id_para = context
    else:
        info_para = context
        id_para = context.id

    group_name, group_link = get_group_info(client, info_para)
    text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
            f"群组名称：{general_link(group_name, group_link)}\n"
            f"群组 ID：{code(id_para)}\n")

    return text


def leave_group(client: Client, gid: int) -> bool:
    # Leave a group, clear it's data
    thread(leave_chat, (client, gid))
    glovar.admin_ids.pop(gid, None)
    glovar.configs.pop(gid, None)
    save("admin_ids")
    save("configs")

    return True
