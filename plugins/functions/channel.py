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
from typing import List, Union

from pyrogram import Client

from .. import glovar
from .etc import format_data, thread
from .file import crypt_file
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
