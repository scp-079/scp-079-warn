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
from json import loads

from pyrogram import Client
from pyrogram.types import CallbackQuery

from plugins.functions.etc import thread
from plugins.functions.filters import authorized_group, class_c
from plugins.functions.telegram import answer_callback
from plugins.functions.user import mention_answer, report_answer, undo_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_callback_query(authorized_group & class_c)
def answer(client: Client, callback_query: CallbackQuery) -> bool:
    # Answer the callback query
    try:
        # Basic data
        gid = callback_query.message.chat.id
        aid = callback_query.from_user.id
        mid = callback_query.message.message_id
        callback_data = loads(callback_query.data)
        action = callback_data["a"]
        action_type = callback_data["t"]
        data = callback_data["d"]

        # Undo
        if action == "undo":
            uid = data
            text = undo_user(client, callback_query.message, aid, uid, action_type)

        # Mention abuse
        elif action == "mention":
            uid = data
            text = mention_answer(client, callback_query.message, aid, uid, action_type)

        # Answer report
        elif action == "report":
            key = data
            text = report_answer(client, callback_query.message, gid, aid, mid, action_type, key)

        else:
            text = ""

        thread(answer_callback, (client, callback_query.id, text))

        return True
    except Exception as e:
        logger.warning(f"Answer callback error: {e}", exc_info=True)

    return False
