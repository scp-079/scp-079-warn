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
from ..functions.etc import get_text, thread
from ..functions.filters import class_c, class_e, test_group
from ..functions.telegram import send_message
from ..functions.users import report_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~test_group & ~class_c & ~class_e & ~Filters.service
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def auto_report(client, message):
    try:
        gid = message.chat.id
        if glovar.modes[gid]["report"]["auto"]:
            text = get_text(message)
            if text:
                if glovar.compiled["bad"].search(text):
                    uid = message.from_user.id
                    mid = message.message_id
                    text, markup = report_user(gid, uid, 0, mid)
                    thread(send_message, (client, gid, text, mid, markup))
    except Exception as e:
        logger.warning(f"Auto report error: {e}", exc_info=True)
