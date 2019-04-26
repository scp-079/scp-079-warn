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
from ..functions.etc import bold, thread, user_mention
from ..functions.filters import class_c, test_group
from ..functions.ids import init_user_id
from ..functions.users import ban_user, forgive_user, get_admin_text, get_class_d_id, get_reason, report_user, warn_user

from ..functions.telegram import delete_messages, send_message, send_report_message


# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~class_c
                   & Filters.command(["admin", "admins"], glovar.prefix))
def admin(client, message):
    try:
        gid = message.chat.id
        if glovar.modes[gid]["mention"]:
            mid = message.message_id
            uid = message.from_user.id
            if (uid
                    and gid not in glovar.user_ids[uid]["waiting"]
                    and gid not in glovar.user_ids[uid]["ban"]):
                text = (f"来自用户：{user_mention(uid)}\n"
                        f"呼叫管理：{get_admin_text(gid)}")
                command_list = message.command
                if len(command_list) < 1:
                    mids = [mid]
                    thread(delete_messages, (client, gid, mids))
                    mid = None

                sent_message = send_message(client, gid, text, mid)
                if sent_message:
                    old_mid = glovar.message_ids.get(gid, 0)
                    if old_mid:
                        mids = [old_mid]
                        thread(delete_messages, (client, gid, mids))

                    sent_mid = sent_message.message_id
                    glovar.message_ids[gid] = sent_mid
    except Exception as e:
        logger.warning(f"Admin error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & class_c
                   & Filters.command(["ban"], glovar.prefix))
def ban(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        uid, re_mid = get_class_d_id(message)
        if uid:
            aid = message.from_user.id
            text, markup = ban_user(client, gid, uid, aid)
            if markup:
                secs = 60
                text = get_reason(message, text)
            else:
                secs = 10

            thread(send_report_message, (secs, client, gid, text, None, markup))
            if re_mid:
                mids = [re_mid, mid]
            else:
                mids = [mid]

            thread(delete_messages, (client, gid, mids))
    except Exception as e:
        logger.warning(f"Ban error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & class_c
                   & Filters.command(["forgive"], glovar.prefix))
def forgive(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        aid = message.from_user.id
        uid = get_class_d_id(message)
        if uid:
            text, result = forgive_user(client, gid, uid, aid)
            if result:
                secs = 60
                text = get_reason(message, text)
            else:
                secs = 10

            thread(send_report_message, (secs, client, gid, text, mid))
    except Exception as e:
        logger.warning(f"Forgive error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~class_c
                   & Filters.command(["report"], glovar.prefix))
def report(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        rid = message.from_user.id
        init_user_id(rid)
        uid, re_mid = get_class_d_id(message)
        init_user_id(uid)
        if (uid
                and gid not in glovar.user_ids[rid]["waiting"]
                and gid not in glovar.user_ids[uid]["waiting"]
                and gid not in glovar.user_ids[uid]["ban"]):
            text, markup = report_user(gid, uid, rid, re_mid)
            if markup:
                secs = 60
            else:
                secs = 10

            thread(send_report_message, (secs, client, gid, text, mid, markup))
    except Exception as e:
        logger.warning(f"Report error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & class_c
                   & Filters.command(["warn"], glovar.prefix))
def warn(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        aid = message.from_user.id
        uid, re_mid = get_class_d_id(message)
        if uid:
            text, markup = warn_user(client, gid, uid, aid)
            if markup:
                secs = 60
                text = get_reason(message, text)
            else:
                secs = 10

            thread(send_report_message, (secs, client, gid, text, mid, markup))
            if re_mid:
                mids = [re_mid, mid]
            else:
                mids = [mid]

            thread(delete_messages, (client, gid, mids))
    except Exception as e:
        logger.warning(f"Warn error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["version"], glovar.prefix))
def version(client, message):
    try:
        cid = message.chat.id
        mid = message.message_id
        text = f"版本：{bold(glovar.version)}"
        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)
