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
from typing import Optional

from pyrogram import Client, Message

from .. import glovar
from .etc import thread
from .file import save
from .telegram import delete_messages, get_messages, leave_chat

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


def get_message(client: Client, gid: int, mid: int) -> Optional[Message]:
    # Get a single message
    result = None
    try:
        mids = [mid]
        result = get_messages(client, gid, mids)
        if result:
            result = result[0]
    except Exception as e:
        logger.warning(f"Get message error: {e}", exc_info=True)

    return result


def leave_group(client: Client, gid: int) -> bool:
    # Leave a group, clear it's data
    try:
        glovar.left_group_ids.add(gid)
        thread(leave_chat, (client, gid))

        glovar.admin_ids.pop(gid, None)
        save("admin_ids")

        glovar.message_ids.pop(gid, 0)
        save("message_ids")

        glovar.configs.pop(gid, None)
        save("configs")

        return True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

    return False
