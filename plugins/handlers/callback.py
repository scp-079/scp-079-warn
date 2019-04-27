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

from .. import glovar
from ..functions.etc import code, delay, thread, user_mention
from ..functions.file import save
from ..functions.filters import class_c
from ..functions.ids import init_user_id
from ..functions.telegram import answer_callback, delete_messages, edit_message_text
from ..functions.user import ban_user, unban_user, unwarn_user, warn_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_callback_query(class_c)
def answer(client, callback_query):
    try:
        gid = callback_query.message.chat.id
        aid = callback_query.from_user.id
        mid = callback_query.message.message_id
        callback_data = loads(callback_query.data)
        action = callback_data["a"]
        action_type = callback_data["t"]
        if action == "undo":
            uid = callback_data["d"]
            init_user_id(uid)
            if gid not in glovar.user_ids[uid]["locked"]:
                try:
                    glovar.user_ids[uid]["locked"].add(gid)
                    if action_type == "ban":
                        text = unban_user(client, gid, uid, aid)
                    else:
                        text = unwarn_user(client, gid, uid, aid)

                    thread(edit_message_text, (client, gid, mid, text))
                finally:
                    glovar.user_ids[uid]["locked"].discard(gid)
                    save("user_ids")
            else:
                thread(answer_callback, (client, callback_query.id, "已被其他管理员处理"))
        elif action == "report":
            report_key = callback_data["d"]
            report_record = glovar.report_records.get(report_key)
            if report_record:
                rid = glovar.report_records[report_key]["reporter"]
                uid = glovar.report_records[report_key]["user"]
                r_mid = glovar.report_records[report_key]["message"]
                init_user_id(rid)
                init_user_id(uid)
                if gid not in glovar.user_ids[uid]["locked"] and gid not in glovar.user_ids[rid]["locked"]:
                    try:
                        glovar.user_ids[rid]["locked"].add(gid)
                        glovar.user_ids[uid]["locked"].add(gid)
                        if action_type == "ban":
                            text, markup = ban_user(client, gid, uid, aid)
                            mids = [r_mid]
                            thread(delete_messages, (client, gid, mids))
                        elif action_type == "warn":
                            text, markup = warn_user(client, gid, uid, aid)
                            mids = [r_mid]
                            thread(delete_messages, (client, gid, mids))
                        elif action_type == "spam":
                            text, markup = warn_user(client, gid, rid, aid)
                            text += f"\n原因：{code('滥用')}"
                        else:
                            text = (f"被举报用户：{user_mention(uid)}\n"
                                    f"管理员：{user_mention(aid)}\n"
                                    f"状态：{code('已取消')}")
                            markup = None

                        if markup:
                            secs = 60
                        else:
                            secs = 10

                        thread(edit_message_text, (client, gid, mid, text, markup))
                        mids = [mid]
                        delay(secs, delete_messages, [client, gid, mids])
                    finally:
                        glovar.user_ids[uid]["locked"].discard(gid)
                        glovar.user_ids[rid]["locked"].discard(gid)
                        save("user_ids")

                    glovar.report_records.pop(report_key)
                else:
                    thread(answer_callback, (client, callback_query.id, "已被其他管理员处理"))
            else:
                text = (f"管理员：{user_mention(aid)}\n"
                        f"状态：{code('已失效')}")
                thread(edit_message_text, (client, gid, mid, text))
                mids = [mid]
                delay(10, delete_messages, [client, gid, mids])
    except Exception as e:
        logger.warning(f"Answer callback error: {e}", exc_info=True)
