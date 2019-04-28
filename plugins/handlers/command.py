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
import re
from time import time
from copy import deepcopy

from pyrogram import Client, Filters

from .. import glovar
from ..functions.etc import bold, code, get_command_context, send_data, thread, user_mention
from ..functions.file import save
from ..functions.filters import class_c, is_class_c, test_group
from ..functions.ids import init_user_id
from ..functions.user import ban_user, forgive_user, get_admin_text, get_class_d_id, get_reason, report_user
from ..functions.user import send_debug, warn_user

from ..functions.telegram import delete_messages, get_group_info, send_message, send_report_message


# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~class_c
                   & Filters.command(["admin", "admins"], glovar.prefix))
def admin(client, message):
    try:
        gid = message.chat.id
        if glovar.configs[gid]["mention"]:
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


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command(["ban"], glovar.prefix))
def ban(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        mids = [mid]
        if is_class_c(None, message):
            uid, re_mid = get_class_d_id(message)
            if uid:
                aid = message.from_user.id
                text, markup = ban_user(client, gid, uid, aid)
                if markup:
                    secs = 60
                    text = get_reason(message, text)
                    send_debug(client, message, "封禁", uid, aid)
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


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command(["config"], glovar.prefix))
def config(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            command_list = list(filter(None, message.command))
            if len(command_list) == 2 and re.search("^warn$", command_list[1], re.I):
                now = int(time())
                if now - glovar.configs[gid]["locked"] > 360:
                    glovar.configs[gid]["locked"] = now
                    group_name, group_link = get_group_info(client, message.chat)
                    exchange_text = send_data(
                        sender="WARN",
                        receivers=["CONFIG"],
                        action="config",
                        action_type="ask",
                        data={
                            "group_id": gid,
                            "group_name": group_name,
                            "group_link": group_link,
                            "user_id": message.from_user.id,
                            "config": glovar.configs[gid]
                        }
                    )
                    thread(send_message, (client, glovar.exchange_channel_id, exchange_text))

        mids = [mid]
        thread(delete_messages, (client, gid, mids))
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & class_c
                   & Filters.command(["forgive"], glovar.prefix))
def forgive(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        mids = [mid]
        if is_class_c(None, message):
            aid = message.from_user.id
            uid, _ = get_class_d_id(message)
            if uid:
                text, result = forgive_user(client, gid, uid, aid)
                glovar.user_ids[uid]["locked"].discard(gid)
                glovar.user_ids[uid]["waiting"].discard(gid)
                save("user_ids")
                if result:
                    secs = 60
                    text = get_reason(message, text)
                else:
                    secs = 10

                thread(send_report_message, (secs, client, gid, text, mid))

        thread(delete_messages, (client, gid, mids))
    except Exception as e:
        logger.warning(f"Forgive error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~class_c
                   & Filters.command(["report"], glovar.prefix))
def report(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        mids = [mid]
        rid = message.from_user.id
        init_user_id(rid)
        uid, re_mid = get_class_d_id(message)
        init_user_id(uid)
        if (uid
                and gid not in glovar.user_ids[rid]["waiting"]
                and gid not in glovar.user_ids[uid]["waiting"]
                and gid not in glovar.user_ids[uid]["ban"]):
            text, markup = report_user(gid, uid, rid, re_mid)
            thread(send_message, (client, gid, text, mid, markup))

        thread(delete_messages, (client, gid, mids))
    except Exception as e:
        logger.warning(f"Report error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command(["warn"], glovar.prefix))
def warn(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        mids = [mid]
        if is_class_c(None, message):
            aid = message.from_user.id
            uid, re_mid = get_class_d_id(message)
            if uid:
                text, markup = warn_user(client, gid, uid, aid)
                if markup:
                    secs = 60
                    text = get_reason(message, text)
                    send_debug(client, message, "警告", uid, aid)
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


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command(["warn_config"], glovar.prefix))
def warn_config(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            aid = message.from_user.id
            command_list = message.command
            success = True
            reason = "已更新"
            new_config = deepcopy(glovar.configs[gid])
            text = f"管理员：{user_mention(aid)}\n"
            if len(command_list) > 1:
                now = int(time())
                if now - glovar.configs[gid]["locked"] > 360:
                    command_type = list(filter(None, command_list))[1]
                    if command_type == "show":
                        text += (f"操作：{code('查看设置')}\n"
                                 f"设置：{code((lambda x: '默认' if x else '自定义')(new_config['default']))}\n"
                                 f"警告上限：{code(new_config['limit'])}\n"
                                 f"呼叫管理：{code((lambda x: '启用' if x else '禁用')(new_config['mention']))}\n"
                                 f"自动举报：{code((lambda x: '启用' if x else '禁用')(new_config['report']['auto']))}\n"
                                 f"手动举报："
                                 f"{code((lambda x: '启用' if x else '禁用')(new_config['report']['manual']))}")
                        thread(send_report_message, (15, client, gid, text))
                        return
                    elif command_type == "default":
                        if not glovar.configs[gid]["default"]:
                            new_config = glovar.default_config
                    else:
                        command_context = get_command_context(message)
                        if command_context:
                            if command_type == "limit":
                                try:
                                    limit = int(command_context)
                                    if 2 <= limit <= 5:
                                        new_config["limit"] = limit
                                    else:
                                        success = False
                                        reason = "数值超过范围"
                                except Exception as e:
                                    logger.info(f"Convert limit context error: {e}")
                                    success = False
                                    reason = "错误的数值"
                            elif command_type == "mention":
                                if command_context == "off":
                                    new_config["mention"] = False
                                elif command_context == "on":
                                    new_config["mention"] = True
                                else:
                                    success = False
                                    reason = "呼叫选项有误"
                            elif command_type == "report":
                                if command_context == "off":
                                    new_config["report"]["auto"] = False
                                    new_config["report"]["manual"] = False
                                elif command_context == "auto":
                                    new_config["report"]["auto"] = True
                                    new_config["report"]["manual"] = False
                                elif command_context == "manual":
                                    new_config["report"]["auto"] = False
                                    new_config["report"]["manual"] = True
                                elif command_context == "both":
                                    new_config["report"]["auto"] = True
                                    new_config["report"]["manual"] = True
                                else:
                                    success = False
                                    reason = "举报选项有误"
                            else:
                                success = False
                                reason = "命令类别有误"
                        else:
                            success = False
                            reason = "命令选项缺失"

                        if success:
                            new_config["default"] = False
                else:
                    success = False
                    reason = "设置当前被锁定"
            else:
                success = False
                reason = "格式有误"

            if success and new_config != glovar.configs[gid]:
                glovar.configs[gid] = new_config
                save("configs")

            text += (f"操作：{code('更改设置')}\n"
                     f"状态：{code(reason)}")
            thread(send_report_message, ((lambda x: 10 if x else 5)(success), client, gid, text))

        mids = [mid]
        thread(delete_messages, (client, gid, mids))
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)


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
