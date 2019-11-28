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
from copy import deepcopy

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import get_debug_text, share_data
from ..functions.etc import bold, code, delay, get_callback_data, get_command_context, get_command_type
from ..functions.etc import get_int, get_now, mention_id, thread
from ..functions.file import save
from ..functions.filters import authorized_group, from_user, is_class_c, test_group
from ..functions.group import delete_message, get_message
from ..functions.ids import init_user_id
from ..functions.user import ban_user, forgive_user, get_admin_text, get_class_d_id, kick_user
from ..functions.user import report_answer, report_user, unban_user, undo_user, warn_user
from ..functions.telegram import get_group_info, resolve_username, send_message, send_report_message

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["admin", "admins"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def admin(client: Client, message: Message) -> bool:
    # Mention admins
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
                        text = (f"来自用户：{mention_id(uid)}\n"
                                f"呼叫管理：{get_admin_text(gid)}\n")
                        reason = get_command_type(message)
                        if reason:
                            text += f"原因：{code(reason)}\n"

                        if message.reply_to_message:
                            rid = message.reply_to_message.message_id
                        else:
                            rid = None

                        result = send_message(client, gid, text, rid)
                        if result:
                            old_mid, _ = glovar.message_ids.get(gid, (0, 0))
                            if old_mid:
                                thread(delete_message, (client, gid, old_mid))

                            sent_mid = result.message_id
                            glovar.message_ids[gid] = (sent_mid, get_now())
                            save("message_ids")

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Admin error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & ~test_group & authorized_group
                   & from_user
                   & Filters.command(["ban"], glovar.prefix))
def ban(client: Client, message: Message) -> bool:
    # Ban users
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            uid, re_mid = get_class_d_id(message)
            if uid and uid not in glovar.admin_ids[gid]:
                aid = message.from_user.id
                reason = get_command_type(message)
                text, markup = ban_user(client, message, uid, aid, 0, reason)
                if markup:
                    secs = 180
                else:
                    secs = 15

                thread(send_report_message, (secs, client, gid, text, None, markup))
                if re_mid:
                    thread(delete_message, (client, gid, re_mid))

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Ban error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & ~test_group & authorized_group
                   & from_user
                   & Filters.command(["config"], glovar.prefix))
def config(client: Client, message: Message) -> bool:
    # Request CONFIG session
    try:
        gid = message.chat.id
        mid = message.message_id
        # Check permission
        if is_class_c(None, message):
            # Check command format
            command_type = get_command_type(message)
            if command_type and re.search(f"^{glovar.sender}$", command_type, re.I):
                now = get_now()
                # Check the config lock
                if now - glovar.configs[gid]["lock"] > 310:
                    # Set lock
                    glovar.configs[gid]["lock"] = now
                    save("configs")
                    # Ask CONFIG generate a config session
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
                    # Send a report message to debug channel
                    text = get_debug_text(client, message.chat)
                    text += (f"群管理：{code(message.from_user.id)}\n"
                             f"操作：{code('创建设置会话')}\n")
                    thread(send_message, (client, glovar.debug_channel_id, text))

            delay(3, delete_message, [client, gid, mid])
        else:
            thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & ~test_group & authorized_group
                   & from_user
                   & Filters.command(["config_warn"], glovar.prefix))
def config_directly(client: Client, message: Message) -> bool:
    # Config the bot directly
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            aid = message.from_user.id
            success = True
            reason = "已更新"
            new_config = deepcopy(glovar.configs[gid])
            text = f"管理员：{code(aid)}\n"
            # Check command format
            command_type, command_context = get_command_context(message)
            if command_type:
                if command_type == "show":
                    report_auto = new_config.get("report") and new_config["report"].get("auto")
                    report_manual = new_config.get("report") and new_config["report"].get("manual")
                    text += (f"操作：{code('查看设置')}\n"
                             f"设置：{code((lambda x: '默认' if x else '自定义')(new_config.get('default')))}\n"
                             f"警告上限：{code(new_config['limit'])}\n"
                             f"协助删除：{code((lambda x: '启用' if x else '禁用')(new_config.get('delete')))}\n"
                             f"呼叫管理：{code((lambda x: '启用' if x else '禁用')(new_config.get('mention')))}\n"
                             f"自动举报：{code((lambda x: '启用' if x else '禁用')(report_auto))}\n"
                             f"手动举报：{code((lambda x: '启用' if x else '禁用')(report_manual))}\n")
                    thread(send_report_message, (30, client, gid, text))
                    thread(delete_message, (client, gid, mid))
                    return True

                now = get_now()
                if now - new_config["lock"] > 310:
                    if command_type == "default":
                        if not new_config.get("default"):
                            new_config = deepcopy(glovar.default_config)
                    else:
                        if command_context:
                            if command_type == "limit":
                                limit = get_int(command_context)
                                if 2 <= limit <= 5:
                                    new_config["limit"] = limit
                                else:
                                    success = False
                                    reason = "命令参数有误"
                            elif command_type in {"delete", "mention"}:
                                if command_context == "off":
                                    new_config[command_type] = False
                                elif command_context == "on":
                                    new_config[command_type] = True
                                else:
                                    success = False
                                    reason = "命令参数有误"
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
                                    reason = "命令参数有误"
                            else:
                                success = False
                                reason = "命令类别有误"
                        else:
                            success = False
                            reason = "命令参数缺失"

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

        return True
    except Exception as e:
        logger.warning(f"Config directly error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & ~test_group & authorized_group
                   & from_user
                   & Filters.command(["forgive"], glovar.prefix))
def forgive(client: Client, message: Message) -> bool:
    # Forgive users
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            uid, _ = get_class_d_id(message)
            if uid and uid not in glovar.admin_ids[gid]:
                reason = get_command_type(message)
                text, success = forgive_user(client, message, uid, reason)
                glovar.user_ids[uid]["lock"].discard(gid)
                save("user_ids")
                if success:
                    secs = 180
                else:
                    secs = 15

                thread(send_report_message, (secs, client, gid, text, None))

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Forgive error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & ~test_group & authorized_group
                   & from_user
                   & Filters.command(["kick"], glovar.prefix))
def kick(client: Client, message: Message) -> bool:
    # Kick users
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            uid, re_mid = get_class_d_id(message)
            if uid and uid not in glovar.admin_ids[gid]:
                aid = message.from_user.id
                reason = get_command_type(message)
                text, success = kick_user(client, message, uid, aid, reason)
                if success:
                    secs = 180
                else:
                    secs = 15

                thread(send_report_message, (secs, client, gid, text))
                if re_mid:
                    thread(delete_message, (client, gid, re_mid))

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Kick error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & ~test_group & authorized_group
                   & from_user
                   & Filters.command(["report"], glovar.prefix))
def report(client: Client, message: Message) -> bool:
    # Report spam messages
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
                        and gid not in glovar.user_ids[rid]["lock"]
                        and gid not in glovar.user_ids[uid]["lock"]
                        and gid not in glovar.user_ids[rid]["waiting"]
                        and gid not in glovar.user_ids[uid]["waiting"]
                        and gid not in glovar.user_ids[uid]["ban"]):
                    # Reporter cannot report someone by replying WARN's report
                    r_message = message.reply_to_message
                    if not r_message.from_user.is_self:
                        reason = get_command_type(message)
                        text, markup, key = report_user(gid, r_message.from_user, rid, re_mid, reason)
                        result = send_message(client, gid, text, re_mid, markup)
                        if result:
                            glovar.reports[key]["report_id"] = result.message_id
                        else:
                            glovar.reports.pop(key, {})

                        save("reports")
        else:
            aid = message.from_user.id
            text = f"管理员：{code(aid)}\n"
            action_type, reason = get_command_context(message)
            if action_type in {"warn", "ban", "cancel", "abuse"}:
                if message.reply_to_message:
                    r_message = get_message(client, gid, message.reply_to_message.message_id)
                    if r_message and r_message.reply_to_message:
                        callback_data_list = get_callback_data(r_message)
                        if callback_data_list and callback_data_list[0]["a"] == "report":
                            key = callback_data_list[0]["d"]
                            report_answer(
                                client=client,
                                message=r_message,
                                gid=gid,
                                aid=aid,
                                mid=r_message.message_id,
                                action_type=action_type,
                                key=key,
                                reason=reason
                            )
                            thread(delete_message, (client, gid, mid))
                            return True
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

        return True
    except Exception as e:
        logger.warning(f"Report error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & ~test_group & authorized_group
                   & from_user
                   & Filters.command(["unban"], glovar.prefix))
def unban(client: Client, message: Message) -> bool:
    # Unban a user
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            aid = message.from_user.id
            text = f"管理员：{code(aid)}\n"
            command_type, command_context = get_command_context(message)
            if command_type:
                uid = get_int(command_context)
                if not uid:
                    peer_type, peer_id = resolve_username(client, command_type)
                    if peer_type == "user" and peer_id:
                        uid = peer_id

                if uid:
                    text = unban_user(client, gid, uid, aid)
                else:
                    text += (f"状态：{code('未操作')}\n"
                             f"原因：{code('命令参数有误')}\n")
            else:
                text += (f"状态：{code('未操作')}\n"
                         f"原因：{code('用法有误')}\n")

            thread(send_report_message, (15, client, gid, text))

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Unban error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & ~test_group & authorized_group
                   & from_user
                   & Filters.command(["undo"], glovar.prefix))
def undo(client: Client, message: Message) -> bool:
    # Undo operations
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            aid = message.from_user.id
            text = f"管理员：{code(aid)}\n"
            if message.reply_to_message:
                r_message = message.reply_to_message
                callback_data_list = get_callback_data(r_message)
                if r_message.from_user.is_self and callback_data_list and callback_data_list[0]["a"] == "undo":
                    action_type = callback_data_list[0]["t"]
                    uid = callback_data_list[0]["d"]
                    undo_user(client, r_message, aid, uid, action_type)
                    thread(delete_message, (client, gid, mid))
                    return True
                else:
                    text += (f"状态：{code('未操作')}\n"
                             f"原因：{code('来源有误')}\n")
            else:
                text += (f"状态：{code('未操作')}\n"
                         f"原因：{code('用法有误')}\n")

            thread(send_report_message, (15, client, gid, text))

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Undo error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & test_group
                   & from_user
                   & Filters.command(["version"], glovar.prefix))
def version(client: Client, message: Message) -> bool:
    # Check the program's version
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"管理员：{mention_id(aid)}\n\n"
                f"版本：{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & ~test_group & authorized_group
                   & from_user
                   & Filters.command(["warn"], glovar.prefix))
def warn(client: Client, message: Message) -> bool:
    # Warn users
    try:
        gid = message.chat.id
        mid = message.message_id
        if is_class_c(None, message):
            aid = message.from_user.id
            uid, re_mid = get_class_d_id(message)
            if uid and uid not in glovar.admin_ids[gid]:
                reason = get_command_type(message)
                text, markup = warn_user(client, message, uid, aid, reason)
                if markup:
                    secs = 180
                else:
                    secs = 15

                thread(send_report_message, (secs, client, gid, text, None, markup))
                if re_mid:
                    thread(delete_message, (client, gid, re_mid))

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Warn error: {e}", exc_info=True)

    return False
