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
from .etc import button_data, code, get_text, message_link, random_str, send_data, thread, user_mention
from .file import save
from .filters import is_class_c
from .ids import init_user_id
from .telegram import kick_chat_member, send_message, unban_chat_member

# Enable logging
logger = logging.getLogger(__name__)


def ban_user(client: Client, gid: int, uid: int, aid: int) -> (str, InlineKeyboardMarkup):
    text = ""
    markup = None
    try:
        init_user_id(uid)
        if gid not in glovar.user_ids[uid]["ban"]:
            thread(kick_chat_member, (client, gid, uid))
            glovar.user_ids[uid]["ban"].add(gid)
            glovar.user_ids[uid]["warn"].pop(gid, 0)
            update_score(client, uid)
            text = (f"已封禁用户：{user_mention(uid)}\n"
                    f"管理员：{user_mention(aid)}")
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
        else:
            text = (f"用户：{user_mention(uid)}\n"
                    f"结果：{code('未操作')}\n"
                    f"原因：{code('已在封禁列表中')}\n"
                    f"管理员：{user_mention(aid)}")
            markup = None

        ask_for_help(client, "delete", gid, uid)
    except Exception as e:
        logger.warning(f"Ban user error: {e}", exc_info=True)

    return text, markup


def forgive_user(client: Client, gid: int, uid: int, aid: int) -> (str, bool):
    text = ""
    result = False
    try:
        init_user_id(uid)
        if gid not in glovar.user_ids[uid]["ban"]:
            if glovar.user_ids[uid]["warn"].get(gid, 0):
                glovar.user_ids[uid]["warn"].pop(gid, 0)
                text = (f"用户：{user_mention(uid)}\n"
                        f"结果：{code('已清空警告')}\n"
                        f"管理员：{user_mention(aid)}")
                result = True
            else:
                text = (f"用户：{user_mention(uid)}\n"
                        f"结果：{code('未操作')}\n"
                        f"原因：{code('未在记录列表中')}\n"
                        f"管理员：{user_mention(aid)}")
                return text, False
        else:
            glovar.user_ids[uid]["ban"].discard(gid)
            thread(unban_chat_member, (client, gid, uid))
            text = (f"用户：{user_mention(uid)}\n"
                    f"结果：{code('已解禁')}\n"
                    f"管理员：{user_mention(aid)}")
            result = True

        update_score(client, gid)
    except Exception as e:
        logger.warning(f"Forgive user error: {e}")

    return text, result


def report_user(gid: int, uid: int, rid: int, mid: int) -> (str, InlineKeyboardMarkup):
    text = ""
    markup = None
    try:
        glovar.user_ids[uid]["waiting"].add(gid)
        report_key = random_str(8)
        while glovar.report_records.get(report_key):
            report_key = random_str(8)

        glovar.report_records[report_key] = {
            "r": rid,
            "u": uid
        }
        if rid:
            glovar.user_ids[rid]["waiting"].add(rid)
            reporter_text = user_mention(rid)
        else:
            reporter_text = code("自动触发")

        save("user_ids")
        text = (f"被举报用户：{user_mention(uid)}\n"
                f"被举报消息：{message_link(gid, mid)}\n"
                f"举报人：{reporter_text}\n"
                f"呼叫管理：{get_admin_text(gid)}")
        warn_data = button_data("report", "warn", report_key)
        ban_data = button_data("report", "ban", report_key)
        cancel_data = button_data("report", "cancel", report_key)
        warn_reporter_data = button_data("report", "spam", report_key)
        markup = InlineKeyboardMarkup(
            [
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
                    ),
                    InlineKeyboardButton(
                        "滥用",
                        callback_data=warn_reporter_data
                    )
                ]
            ]
        )
    except Exception as e:
        logger.warning(f"Report user error: {e}", exc_info=True)

    return text, markup


def get_admin_text(gid: int) -> str:
    mention_text = ""
    try:
        admin_list = list(glovar.admin_ids[gid])
        admin_count = len(admin_list)
        mention_style = ["A", "D", "M", "I", "N", "S"]
        mention_count = len(mention_style)
        if admin_count < mention_count:
            admin_list += admin_list[0] * (mention_count - admin_count)

        mention_list = sample(admin_list, mention_count)
        mention_text = ""
        for i in range(mention_count):
            mention_text += f"[{mention_style[i]}](tg://user?id={mention_list[i]})"
    except Exception as e:
        logging.warning(f"Get admin text error: {e}", exc_info=True)

    return mention_text


def get_class_d_id(message: Message) -> (int, int):
    uid, mid = (0, 0)
    try:
        r_message = message.reply_to_message
        if r_message:
            if not is_class_c(None, r_message):
                uid = r_message.from_user.id
                mid = r_message.message_id
            elif r_message.reply_to_message.from_user.is_self:
                uid = int(r_message.text.partition("\n")[0].partition("：")[2])
    except Exception as e:
        logger.warning(f"Get class d id error: {e}", exc_info=True)

    return uid, mid


def get_reason(message: Message, text: str) -> str:
    try:
        command_list = list(filter(None, message.command))
        reason = get_text(message)[len(command_list[0]) + 1:].strip()
        if reason:
            text += f"\n原因：{code(reason)}"
    except Exception as e:
        logging.warning(f"Get reason error: {e}", exc_info=True)

    return text


def ask_for_help(client: Client, level: str, gid: int, uid: int) -> bool:
    try:
        data = send_data(
            sender="WARN",
            receivers=["USER"],
            action="help",
            action_type=level,
            data={
                "group_id": gid,
                "user_id": uid
            }
        )
        thread(send_message, (client, glovar.exchange_channel_id, data))
        return True
    except Exception as e:
        logger.warning(f"Ask for help error: {e}", exc_info=True)

    return False


def warn_user(client: Client, gid: int, uid: int, aid: int) -> (str, InlineKeyboardMarkup):
    text = ""
    markup = None
    try:
        init_user_id(uid)
        if gid not in glovar.user_ids[uid]["ban"]:
            if not glovar.user_ids[uid]["warn"].get(gid, 0):
                glovar.user_ids[uid]["warn"][gid] = 1
            else:
                glovar.user_ids[uid]["warn"][gid] += 1

            warn_count = glovar.user_ids[uid]["warn"][gid]
            limit = glovar.configs[gid]["limit"]
            if warn_count >= limit:
                ban_user(client, gid, uid, aid)
                text = (f"已封禁用户：{user_mention(uid)}\n"
                        f"原因：{code('警告次数达到上限')}\n"
                        f"管理员：{user_mention(aid)}")
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
                update_score(client, uid)
                text = (f"已警告用户：{user_mention(uid)}\n"
                        f"该用户警告统计：{code(f'{warn_count}/{limit}')}\n"
                        f"管理员：{user_mention(aid)}")
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
        else:
            text = (f"用户：{user_mention(uid)}\n"
                    f"结果：{code('未操作')}\n"
                    f"原因：{code('已在封禁列表中')}\n"
                    f"管理员：{user_mention(aid)}")
            markup = None
    except Exception as e:
        logger.warning(f"Warn user error: {e}", exc_info=True)

    return text, markup


def unban_user(client: Client, gid: int, uid: int, aid: int) -> str:
    text = ""
    try:
        if gid in glovar.user_ids[uid]["ban"]:
            thread(unban_chat_member, (client, gid, uid))
            glovar.user_ids[uid]["ban"].discard(gid)
            update_score(client, uid)
            text = (f"已解禁用户：{user_mention(uid)}\n"
                    f"管理员：{user_mention(aid)}")
        else:
            text = (f"用户：{user_mention(uid)}\n"
                    f"结果：{code('未操作')}\n"
                    f"原因：{code('不在封禁列表中')}\n"
                    f"管理员：{user_mention(aid)}")
    except Exception as e:
        logger.warning(f"Unban user error: {e}", exc_info=True)

    return text


def unwarn_user(client: Client, gid: int, uid: int, aid: int) -> str:
    text = ""
    try:
        if gid not in glovar.user_ids[uid]["ban"]:
            if not glovar.user_ids[uid]["warn"].get(gid, 0):
                text = (f"用户：{user_mention(uid)}\n"
                        f"结果：{code('未操作')}\n"
                        f"原因：{code('无警告记录')}\n"
                        f"管理员：{user_mention(aid)}")
            else:
                glovar.user_ids[uid]["warn"][gid] -= 1
                warn_count = glovar.user_ids[uid]["warn"][gid]
                if warn_count == 0:
                    glovar.user_ids[uid]["warn"].pop(gid, 0)
                    update_score(client, gid)
                    text = (f"已撤销警告：{user_mention(uid)}\n"
                            f"该用户警告统计：{code('无警告')}\n"
                            f"管理员：{user_mention(aid)}")
                else:
                    limit = glovar.configs[gid]["limit"]
                    update_score(client, uid)
                    text = (f"已撤销警告：{user_mention(uid)}\n"
                            f"该用户警告统计：{code(f'{warn_count}/{limit}')}\n"
                            f"管理员：{user_mention(aid)}")
        else:
            text = (f"用户：{user_mention(uid)}\n"
                    f"结果：{code('未操作')}\n"
                    f"原因：{code('已在封禁列表中')}\n"
                    f"管理员：{user_mention(aid)}")
    except Exception as e:
        logger.warning(f"Unwarn user error: {e}", exc_info=True)

    return text


def update_score(client: Client, uid: int) -> bool:
    try:
        ban_count = len(glovar.user_ids[uid]["ban"])
        warn_count = len(glovar.user_ids[uid]["warn"])
        score = ban_count * 1 + warn_count * 0.4
        glovar.user_ids[uid]["score"] = score
        save("user_ids")
        data = send_data(
            sender="WARN",
            receivers=["NOSPAM", "NOPORN"],
            action="update",
            action_type="score",
            data={
                "id": uid,
                "score": score
            }
        )
        thread(send_message, (client, glovar.exchange_channel_id, data))
        return True
    except Exception as e:
        logger.warning(f"Update score error: {e}", exc_info=True)

    return False
