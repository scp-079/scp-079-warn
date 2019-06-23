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
from ..functions.channel import get_debug_text, share_data
from ..functions.etc import bold, code, get_callback_data, get_command_context, get_command_type, get_full_name
from ..functions.etc import thread, user_mention
from ..functions.file import save
from ..functions.filters import is_class_c, test_group
from ..functions.group import delete_message, get_message
from ..functions.ids import init_user_id
from ..functions.user import ban_user, forgive_user, get_admin_text, get_class_d_id, report_answer, report_user
from ..functions.user import undo_user, warn_user
from ..functions.telegram import get_group_info, send_message, send_report_message

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~test_group
                   & Filters.command(["admin", "admins"], glovar.prefix))
def admin(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if not is_class_c(None, message):
            if glovar.configs[gid]["mention"]:
                # Admin can not mention admins
                if not is_class_c(None, message):
                    uid = message.from_user.id
                    init_user_id(uid)
                    # Warned user and the user having report status can't mention admins
                    if (gid not in glovar.user_ids[uid]["waiting"]
                            and gid not in glovar.user_ids[uid]["ban"]
                            and glovar.user_ids[uid]["warn"].get(gid) is None):
                        text = (f"来自用户：{user_mention(uid)}\n"
                                f"呼叫管理：{get_admin_text(gid)}\n")
                        reason = get_command_type(message)
                        if reason:
                            text += f"原因：{code(reason)}\n"

                        if message.reply_to_message:
                            rid = message.reply_to_message.message_id
                        else:
                            rid = None

                        sent_message = send_message(client, gid, text, rid)
                        if sent_message:
                            old_mid = glovar.message_ids.get(gid, 0)
                            if old_mid:
                                thread(delete_message, (client, gid, old_mid))

                            sent_mid = sent_message.message_id
                            glovar.message_ids[gid] = sent_mid
                            save("message_ids")

        thread(delete_message, (client, gid, mid))
    except Exception as e:
        logger.warning(f"Admin error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~test_group
                   & Filters.command(["ban"], glovar.prefix))
def ban(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            uid, re_mid = get_class_d_id(message)
            if uid and uid not in glovar.admin_ids[gid]:
                aid = message.from_user.id
                text, markup = ban_user(client, message, uid, aid)
                if markup:
                    secs = 180
                    reason = get_command_type(message)
                    if reason:
                        text += f"原因：{code(reason)}\n"
                else:
                    secs = 15

                thread(send_report_message, (secs, client, gid, text, None, markup))
                if re_mid:
                    thread(delete_message, (client, gid, re_mid))

        thread(delete_message, (client, gid, mid))
    except Exception as e:
        logger.warning(f"Ban error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~test_group
                   & Filters.command(["config"], glovar.prefix))
def config(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            command_list = list(filter(None, message.command))
            if len(command_list) == 2 and re.search("^warn$", command_list[1], re.I):
                now = int(time())
                if now - glovar.configs[gid]["lock"] > 360:
                    glovar.configs[gid]["lock"] = now
                    group_name, group_link = get_group_info(client, message.chat)
                    share_data(
                        client=client,
                        receivers=["CONFIG"],
                        action="config",
                        action_type="ask",
                        data={
                            "project_name": glovar.project_name,
                            "project_link": glovar.project_link,
                            "group_id": gid,
                            "group_name": group_name,
                            "group_link": group_link,
                            "user_id": message.from_user.id,
                            "config": glovar.configs[gid],
                            "default": glovar.default_config
                        }
                    )
                    text = get_debug_text(client, message.chat)
                    text += (f"群管理：{code(message.from_user.id)}\n"
                             f"操作：{code('创建设置会话')}\n")
                    thread(send_message, (client, glovar.debug_channel_id, text))

        thread(delete_message, (client, gid, mid))
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~test_group
                   & Filters.command(["config_warn"], glovar.prefix))
def config_warn(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            aid = message.from_user.id
            command_list = message.command
            success = True
            reason = "已更新"
            new_config = deepcopy(glovar.configs[gid])
            text = f"管理员：{code(aid)}\n"
            # Check command format
            command_type, command_context = get_command_context(message)
            if command_type:
                now = int(time())
                if now - new_config["lock"] > 360:
                    command_type = list(filter(None, command_list))[1]
                    if command_type == "show":
                        text += (f"操作：{code('查看设置')}\n"
                                 f"设置：{code((lambda x: '默认' if x else '自定义')(new_config['default']))}\n"
                                 f"警告上限：{code(new_config['limit'])}\n"
                                 f"呼叫管理：{code((lambda x: '启用' if x else '禁用')(new_config['mention']))}\n"
                                 f"自动举报：{code((lambda x: '启用' if x else '禁用')(new_config['report']['auto']))}\n"
                                 f"手动举报："
                                 f"{code((lambda x: '启用' if x else '禁用')(new_config['report']['manual']))}\n")
                        thread(send_report_message, (30, client, gid, text))
                        thread(delete_message, (client, gid, mid))
                        return
                    elif command_type == "default":
                        if not new_config.get("default"):
                            new_config = deepcopy(glovar.default_config)
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
                                if not new_config.get("report"):
                                    new_config["report"] = {}

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
                     f"状态：{code(reason)}\n")
            thread(send_report_message, ((lambda x: 10 if x else 5)(success), client, gid, text))

        thread(delete_message, (client, gid, mid))
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~test_group
                   & Filters.command(["forgive"], glovar.prefix))
def forgive(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            aid = message.from_user.id
            uid, _ = get_class_d_id(message)
            if uid and uid not in glovar.admin_ids[gid]:
                text, result = forgive_user(client, gid, uid, aid)
                glovar.user_ids[uid]["locked"].discard(gid)
                save("user_ids")
                if result:
                    secs = 180
                    reason = get_command_type(message)
                    if reason:
                        text += f"原因：{code(reason)}\n"
                else:
                    secs = 15

                thread(send_report_message, (secs, client, gid, text, None))

        thread(delete_message, (client, gid, mid))
    except Exception as e:
        logger.warning(f"Forgive error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~test_group
                   & Filters.command(["report"], glovar.prefix))
def report(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if not is_class_c(None, message):
            if glovar.configs[gid]["report"]["manual"]:
                rid = message.from_user.id
                init_user_id(rid)
                uid, re_mid = get_class_d_id(message)
                init_user_id(uid)
                # Reporter should not be admin or user in waiting list
                if (uid
                        and uid != rid
                        and uid not in glovar.admin_ids[gid]
                        and gid not in glovar.user_ids[rid]["waiting"]
                        and gid not in glovar.user_ids[uid]["waiting"]
                        and gid not in glovar.user_ids[uid]["ban"]):
                    # Reporter cannot report someone by replying WARN's report
                    r_message = message.reply_to_message
                    if not r_message.from_user.is_self:
                        text, markup = report_user(gid, uid, rid, re_mid)
                        reason = get_command_type(message)
                        if reason:
                            text += f"原因：{code(reason)}\n"

                        name = get_full_name(r_message.from_user)
                        if name:
                            text += f"被举报用户昵称：{code(name)}\n"

                        thread(send_message, (client, gid, text, re_mid, markup))
        else:
            aid = message.from_user.id
            text = f"管理员：{code(aid)}\n"
            command_list = list(filter(None, message.command))
            if len(command_list) == 2 and command_list[1] in {"warn", "ban", "cancel", "spam"}:
                command_type = command_list[1]
                if message.reply_to_message:
                    r_message = get_message(client, gid, message.reply_to_message.message_id)
                    if r_message and r_message.reply_to_message:
                        callback_data_list = get_callback_data(r_message)
                        if callback_data_list and callback_data_list[0]["a"] == "report":
                            report_key = callback_data_list[0]["d"]
                            report_answer(client, r_message, gid, aid, r_message.message_id, command_type, report_key)
                            thread(delete_message, (client, gid, mid))
                            return
                        else:
                            text += (f"状态：{code('未操作')}\n"
                                     f"原因：{code('来源有误')}\n")
                    else:
                        text += (f"结果：{code('未操作')}\n"
                                 f"原因：{code('消息已被删除')}\n")
                else:
                    text += (f"状态：{code('未操作')}\n"
                             f"原因：{code('用法有误')}\n")
            else:
                text += (f"状态：{code('未操作')}\n"
                         f"原因：{code('格式有误')}\n")

            thread(send_report_message, (15, client, gid, text))

        thread(delete_message, (client, gid, mid))
    except Exception as e:
        logger.warning(f"Report error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~test_group
                   & Filters.command(["undo"], glovar.prefix))
def undo(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            aid = message.from_user.id
            text = f"管理员：{code(aid)}\n"
            command_list = list(filter(None, message.command))
            if len(command_list) == 1:
                if message.reply_to_message:
                    r_message = message.reply_to_message
                    callback_data_list = get_callback_data(r_message)
                    if r_message.from_user.is_self and callback_data_list and callback_data_list[0]["a"] == "undo":
                        action_type = callback_data_list[0]["t"]
                        uid = callback_data_list[0]["d"]
                        undo_user(client, gid, aid, uid, r_message.message_id, action_type)
                        thread(delete_message, (client, gid, mid))
                        return
                    else:
                        text += (f"状态：{code('未操作')}\n"
                                 f"原因：{code('来源有误')}\n")
                else:
                    text += (f"状态：{code('未操作')}\n"
                             f"原因：{code('用法有误')}\n")

                thread(send_report_message, (15, client, gid, text))

        thread(delete_message, (client, gid, mid))
    except Exception as e:
        logger.warning(f"Undo error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["version"], glovar.prefix))
def version(client, message):
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"管理员：{user_mention(aid)}\n\n"
                f"版本：{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~test_group
                   & Filters.command(["warn"], glovar.prefix))
def warn(client, message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            aid = message.from_user.id
            uid, re_mid = get_class_d_id(message)
            if uid and uid not in glovar.admin_ids[gid]:
                text, markup = warn_user(client, message, uid, aid)
                if markup:
                    secs = 180
                    reason = get_command_type(message)
                    if reason:
                        text += f"原因：{code(reason)}\n"
                else:
                    secs = 15

                thread(send_report_message, (secs, client, gid, text, None, markup))
                if re_mid:
                    thread(delete_message, (client, gid, re_mid))

        thread(delete_message, (client, gid, mid))
    except Exception as e:
        logger.warning(f"Warn error: {e}", exc_info=True)
