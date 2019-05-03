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
from random import sample

from pyrogram import Client, Message, InlineKeyboardButton, InlineKeyboardMarkup

from .. import glovar
from .channel import ask_for_help, forward_evidence, send_debug, update_score
from .etc import button_data, code, general_link, message_link, random_str, thread, user_mention
from .file import save
from .filters import is_class_c
from .ids import init_user_id
from .telegram import kick_chat_member, unban_chat_member

# Enable logging
logger = logging.getLogger(__name__)


def ban_user(client: Client, message: Message, uid: int, aid: int) -> (str, InlineKeyboardMarkup):
    # Ban a user
    text = ""
    markup = None
    try:
        gid = message.chat.id
        init_user_id(uid)
        if gid not in glovar.user_ids[uid]["ban"]:
            result = forward_evidence(client, message.reply_to_message, "封禁用户", "群管自行操作")
            if result:
                thread(kick_chat_member, (client, gid, uid))
                glovar.user_ids[uid]["ban"].add(gid)
                glovar.user_ids[uid]["warn"].pop(gid, 0)
                update_score(client, uid)
                text = f"已封禁用户：{user_mention(uid)}\n"
                data = button_data("undo", "ban", uid)
                markup = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "解禁",
                                callback_data=data
                            )
                        ]
                    ]
                )
                ask_for_help(client, "delete", gid, uid)
                send_debug(client, message, "封禁", uid, aid, result)
        else:
            text = (f"用户：{user_mention(uid)}\n"
                    f"结果：{code('未操作')}\n"
                    f"原因：{code('已在封禁列表中')}\n")
            markup = None

        text += f"管理员：{user_mention(aid)}"
    except Exception as e:
        logger.warning(f"Ban user error: {e}", exc_info=True)

    return text, markup


def forgive_user(client: Client, gid: int, uid: int, aid: int) -> (str, bool):
    # Forgive user
    text = ""
    result = False
    try:
        init_user_id(uid)
        if gid not in glovar.user_ids[uid]["ban"]:
            if glovar.user_ids[uid]["warn"].get(gid, 0):
                glovar.user_ids[uid]["warn"].pop(gid, 0)
                text = (f"用户：{user_mention(uid)}\n"
                        f"结果：{code('已清空警告')}\n")
                result = True
            elif gid in glovar.user_ids[uid]["waiting"]:
                glovar.user_ids[uid]["waiting"].discard(gid)
                save("user_ids")
                text = (f"用户：{user_mention(uid)}\n"
                        f"结果：{code('已重置举报状态')}\n")
                return text, True
            else:
                text = (f"用户：{user_mention(uid)}\n"
                        f"结果：{code('未操作')}\n"
                        f"原因：{code('未在记录列表中')}\n")
                return text, False
        else:
            glovar.user_ids[uid]["ban"].discard(gid)
            thread(unban_chat_member, (client, gid, uid))
            text = (f"用户：{user_mention(uid)}\n"
                    f"结果：{code('已解禁')}\n")
            result = True

        update_score(client, uid)
        text += f"管理员：{user_mention(aid)}"
    except Exception as e:
        logger.warning(f"Forgive user error: {e}")

    return text, result


def get_admin_text(gid: int) -> str:
    # Get admin mention text
    mention_text = ""
    try:
        admin_list = list(glovar.admin_ids[gid])
        if glovar.user_id in admin_list:
            admin_list.remove(glovar.user_id)

        admin_count = len(admin_list)
        mention_style = ["A", "D", "M", "I", "N", "S"]
        mention_count = len(mention_style)
        if admin_count < mention_count:
            admin_list += [admin_list[0]] * (mention_count - admin_count)

        mention_list = sample(admin_list, mention_count)
        mention_text = ""
        for i in range(mention_count):
            mention_text += f"{general_link(mention_style[i], f'tg://user?id={mention_list[i]}')}"
    except Exception as e:
        logging.warning(f"Get admin text error: {e}", exc_info=True)

    return mention_text


def get_class_d_id(message: Message) -> (int, int):
    # Get Class D personnel's id
    uid, mid = (0, 0)
    try:
        r_message = message.reply_to_message
        if r_message:
            if not is_class_c(None, r_message):
                uid = r_message.from_user.id
                mid = r_message.message_id
            elif r_message.from_user.is_self:
                uid = int(r_message.text.partition("\n")[0].partition("：")[2])
                if uid in glovar.admin_ids[message.chat.id]:
                    uid = 0
    except Exception as e:
        logger.warning(f"Get class d id error: {e}", exc_info=True)

    return uid, mid


def report_user(gid: int, uid: int, rid: int, mid: int) -> (str, InlineKeyboardMarkup):
    # Report a user
    text = ""
    markup = None
    try:
        glovar.user_ids[uid]["waiting"].add(gid)
        glovar.user_ids[rid]["waiting"].add(rid)
        save("user_ids")
        report_key = random_str(8)
        while glovar.report_records.get(report_key):
            report_key = random_str(8)

        glovar.report_records[report_key] = {
            "reporter": rid,
            "user": uid,
            "message": mid
        }
        if rid:
            reporter_text = user_mention(rid)
        else:
            reporter_text = code("自动触发")

        text = (f"被举报用户：{user_mention(uid)}\n"
                f"被举报消息：{message_link(gid, mid)}\n"
                f"举报人：{reporter_text}\n"
                f"呼叫管理：{get_admin_text(gid)}\n")
        warn_data = button_data("report", "warn", report_key)
        ban_data = button_data("report", "ban", report_key)
        cancel_data = button_data("report", "cancel", report_key)
        markup_list = [
            [
                InlineKeyboardButton(
                    "警告",
                    callback_data=warn_data
                ),
                InlineKeyboardButton(
                    "封禁",
                    callback_data=ban_data
                )
            ],
            [
                InlineKeyboardButton(
                    "取消",
                    callback_data=cancel_data
                )
            ]
        ]
        if rid:
            warn_reporter_data = button_data("report", "spam", report_key)
            markup_list[1].append(
                InlineKeyboardButton(
                    "滥用",
                    callback_data=warn_reporter_data
                )
            )

        markup = InlineKeyboardMarkup(markup_list)
    except Exception as e:
        logger.warning(f"Report user error: {e}", exc_info=True)

    return text, markup


def warn_user(client: Client, message: Message, uid: int, aid: int) -> (str, InlineKeyboardMarkup):
    # Warn a user
    text = ""
    markup = None
    try:
        gid = message.chat.id
        init_user_id(uid)
        if gid not in glovar.user_ids[uid]["ban"]:
            result = forward_evidence(client, message.reply_to_message, "警告用户", "群管自行操作")
            if result:
                if not glovar.user_ids[uid]["warn"].get(gid, 0):
                    glovar.user_ids[uid]["warn"][gid] = 1
                    update_score(client, uid)
                else:
                    glovar.user_ids[uid]["warn"][gid] += 1

                warn_count = glovar.user_ids[uid]["warn"][gid]
                limit = glovar.configs[gid]["limit"]
                if warn_count >= limit:
                    ban_user(client, message, uid, aid)
                    text = (f"已封禁用户：{user_mention(uid)}\n"
                            f"原因：{code('警告次数达到上限')}\n")
                    data = button_data("undo", "ban", uid)
                    markup = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "解禁",
                                    callback_data=data
                                )
                            ]
                        ]
                    )
                    ask_for_help(client, "delete", gid, uid)
                else:
                    text = (f"已警告用户：{user_mention(uid)}\n"
                            f"该用户警告统计：{code(f'{warn_count}/{limit}')}\n")
                    data = button_data("undo", "warn", uid)
                    markup = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "撤销",
                                    callback_data=data
                                )
                            ]
                        ]
                    )

                send_debug(client, message, "警告", uid, aid, result)
        else:
            text = (f"用户：{user_mention(uid)}\n"
                    f"结果：{code('未操作')}\n"
                    f"原因：{code('已在封禁列表中')}\n")
            markup = None

        text += f"管理员：{user_mention(aid)}\n"
    except Exception as e:
        logger.warning(f"Warn user error: {e}", exc_info=True)

    return text, markup


def unban_user(client: Client, gid: int, uid: int, aid: int) -> str:
    # Unban a user
    text = ""
    try:
        if gid in glovar.user_ids[uid]["ban"]:
            thread(unban_chat_member, (client, gid, uid))
            glovar.user_ids[uid]["ban"].discard(gid)
            update_score(client, uid)
            text = f"已解禁用户：{user_mention(uid)}\n"
        else:
            text = (f"用户：{user_mention(uid)}\n"
                    f"结果：{code('未操作')}\n"
                    f"原因：{code('不在封禁列表中')}\n")

        text += f"管理员：{user_mention(aid)}"
    except Exception as e:
        logger.warning(f"Unban user error: {e}", exc_info=True)

    return text


def unwarn_user(client: Client, gid: int, uid: int, aid: int) -> str:
    # Unwarn a user
    text = ""
    try:
        if gid not in glovar.user_ids[uid]["ban"]:
            if not glovar.user_ids[uid]["warn"].get(gid, 0):
                text = (f"用户：{user_mention(uid)}\n"
                        f"结果：{code('未操作')}\n"
                        f"原因：{code('无警告记录')}\n")
            else:
                glovar.user_ids[uid]["warn"][gid] -= 1
                warn_count = glovar.user_ids[uid]["warn"][gid]
                if warn_count == 0:
                    glovar.user_ids[uid]["warn"].pop(gid, 0)
                    update_score(client, uid)
                    text = (f"已撤销警告：{user_mention(uid)}\n"
                            f"该用户警告统计：{code('无警告')}\n")
                else:
                    limit = glovar.configs[gid]["limit"]
                    text = (f"已撤销警告：{user_mention(uid)}\n"
                            f"该用户警告统计：{code(f'{warn_count}/{limit}')}\n")
        else:
            text = (f"用户：{user_mention(uid)}\n"
                    f"结果：{code('未操作')}\n"
                    f"原因：{code('已在封禁列表中')}\n")

        text += f"管理员：{user_mention(aid)}"
    except Exception as e:
        logger.warning(f"Unwarn user error: {e}", exc_info=True)

    return text
