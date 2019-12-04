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
from time import sleep
from typing import Union

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, Message, User

from .. import glovar
from .channel import ask_for_help, forward_evidence, send_debug, update_score
from .etc import button_data, code, delay, general_link, get_channel_link, get_int, get_now, get_text, lang
from .etc import mention_id, message_link, random_str, thread
from .file import save
from .filters import is_class_c, is_from_user, is_limited_admin
from .group import delete_message
from .ids import init_user_id
from .telegram import edit_message_text, kick_chat_member, unban_chat_member

# Enable logging
logger = logging.getLogger(__name__)


def ban_user(client: Client, message: Message, uid: int, aid: int, result: int = 0,
             reason: str = None) -> (str, InlineKeyboardMarkup):
    # Ban a user
    text = ""
    markup = None
    try:
        # Basic data
        gid = message.chat.id

        # Check admin
        if is_limited_admin(gid, aid):
            return "", None

        # Init user data
        if not init_user_id(uid):
            return "", None

        # Check users' locks
        if gid in glovar.user_ids[uid]["lock"]:
            return "", None

        # Proceed
        glovar.user_ids[uid]["lock"].add(gid)
        try:
            if gid in glovar.user_ids[uid]["ban"]:
                text += (f"{lang('user_id')}{lang('colon')}{mention_id(uid)}\n"
                         f"{lang('action')}{lang('colon')}{code(lang('action_ban'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_banned'))}\n"
                         f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
                return text, None

            if not result:
                result = forward_evidence(
                    client=client,
                    message=message.reply_to_message,
                    level=lang("action_ban")
                )

            if not result:
                text += (f"{lang('user_id')}{lang('colon')}{mention_id(uid)}\n"
                         f"{lang('action')}{lang('colon')}{code(lang('action_ban'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_deleted'))}\n"
                         f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
                return text, None

            # Count admin operation
            glovar.counts[gid][aid] += 1

            # Ban the user
            thread(kick_chat_member, (client, gid, uid))
            glovar.user_ids[uid]["ban"].add(gid)
            glovar.user_ids[uid]["warn"].pop(gid, 0)
            update_score(client, uid)

            # Generate report text
            stored_link = general_link(result.message_id, message_link(result))
            text += (f"{lang('user_banned')}{lang('colon')}{mention_id(uid)}\n"
                     f"{lang('stored_message')}{lang('colon')}{stored_link}\n"
                     f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")

            if reason:
                text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

            # Generate report markup
            data = button_data("undo", "ban", uid)
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=lang("unban"),
                            callback_data=data
                        )
                    ]
                ]
            )

            # Share
            ask_for_help(client, "delete", gid, uid)
            send_debug(
                client=client,
                message=message,
                action=lang("action_ban"),
                uid=uid,
                aid=aid,
                em=result,
                reason=reason
            )
        finally:
            glovar.user_ids[uid]["lock"].discard(gid)
    except Exception as e:
        logger.warning(f"Ban user error: {e}", exc_info=True)

    return text, markup


def forgive_user(client: Client, message: Message, uid: int, reason: str = None) -> (str, bool):
    # Forgive user
    text = ""
    success = False
    try:
        # Basic data
        gid = message.chat.id
        aid = message.from_user.id

        # Init user data
        if not init_user_id(uid):
            return "", False

        # Check users' locks
        if gid in glovar.user_ids[uid]["lock"]:
            return "", False

        # Proceed
        glovar.user_ids[uid]["lock"].add(gid)
        try:
            # Text prefix
            text += f"{lang('user_id')}{lang('colon')}{mention_id(uid)}\n"

            if gid in glovar.user_ids[uid]["ban"]:
                glovar.user_ids[uid]["ban"].discard(gid)
                thread(unban_chat_member, (client, gid, uid))
                text += (f"{lang('action')}{lang('colon')}{code(lang('action_unban'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
                success = True
            elif glovar.user_ids[uid]["warn"].get(gid, 0):
                glovar.user_ids[uid]["warn"].pop(gid, 0)
                text += (f"{lang('action')}{lang('colon')}{code(lang('action_unwarns'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
                success = True
            elif gid in glovar.user_ids[uid]["waiting"]:
                glovar.user_ids[uid]["waiting"].discard(gid)
                text += (f"{lang('action')}{lang('colon')}{code(lang('action_unwait'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
                success = True
            else:
                text += (f"{lang('action')}{lang('colon')}{code(lang('action_forgive'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_none'))}\n")
                success = False

            text += f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n"

            if not success:
                return text, success

            save("user_ids")

            if reason:
                text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

            update_score(client, uid)
            send_debug(
                client=client,
                message=message,
                action=lang("action_forgive"),
                uid=uid,
                aid=aid,
                reason=reason
            )
        finally:
            glovar.user_ids[uid]["lock"].discard(gid)
    except Exception as e:
        logger.warning(f"Forgive user error: {e}")

    return text, success


def get_admin_text(gid: int) -> str:
    # Get admin mention text
    result = ""
    try:
        admin_all_list = list(glovar.admin_ids[gid])
        admin_list = list(filter(lambda a: a not in glovar.bot_ids, admin_all_list))
        admin_count = len(admin_list)
        mention_style = ["A", "D", "M", "I", "N", "S"]
        mention_count = len(mention_style)

        if admin_count < mention_count:
            admin_list += [admin_list[0]] * (mention_count - admin_count)

        mention_list = sample(admin_list, mention_count)
        result = ""

        for i in range(mention_count):
            result += f"{general_link(mention_style[i], f'tg://user?id={mention_list[i]}')}"
    except Exception as e:
        logging.warning(f"Get admin text error: {e}", exc_info=True)

    return result


def get_class_d_id(message: Message) -> (int, int):
    # Get Class D personnel's id
    uid = 0
    mid = 0
    try:
        r_message = message.reply_to_message

        if not r_message or not is_from_user(None, r_message):
            return 0, 0

        if not is_class_c(None, r_message):
            uid = r_message.from_user.id
            mid = r_message.message_id
        elif r_message.from_user.is_self:
            uid = get_int(r_message.text.split("\n")[0].split(lang("colon"))[1])
            if uid in glovar.admin_ids[message.chat.id]:
                uid = 0
    except Exception as e:
        logger.warning(f"Get class d id error: {e}", exc_info=True)

    return uid, mid


def kick_user(client: Client, gid: int, uid: Union[int, str]) -> bool:
    # Kick a user
    try:
        thread(kick_user_thread, (client, gid, uid))

        return True
    except Exception as e:
        logger.warning(f"Kick user error: {e}", exc_info=True)

    return False


def kick_user_thread(client: Client, gid: int, uid: Union[int, str]) -> bool:
    # Kick a user thread
    try:
        kick_chat_member(client, gid, uid)
        sleep(3)
        unban_chat_member(client, gid, uid)

        return True
    except Exception as e:
        logger.warning(f"Kick user thread error: {e}", exc_info=True)

    return False


def mention_answer(client: Client, message: Message, aid: int, uid: int, action_type: str) -> str:
    # Mention abuse
    try:
        # Basic data
        gid = message.chat.id
        mid = message.message_id

        # Abuse
        if action_type == "abuse":
            message.reply_to_message = message
            message.reply_to_message.from_user.id = uid
            message.reply_to_message.from_user.is_self = lang("abuse_mention")
            text, markup = warn_user(client, message, uid, aid)
            text += f"{lang('reason')}{lang('colon')}{code(lang('reason_abuse'))}\n"

            # Edit the report message
            thread(edit_message_text, (client, gid, mid, text, markup))
            delay(180, delete_message, [client, gid, mid])

        # Delete
        elif action_type == "delete":
            glovar.message_ids[gid] = (0, 0)
            save("message_ids")
            delete_message(client, gid, mid)
    except Exception as e:
        logger.warning(f"Mention answer error: {e}", exc_info=True)

    return ""


def remove_user(client: Client, message: Message, uid: int, aid: int,
                reason: str = None) -> (str, bool):
    # Kick a user
    text = ""
    success = False
    try:
        # Basic data
        gid = message.chat.id

        # Check admin
        if is_limited_admin(gid, aid):
            return "", False

        # Init user data
        if not init_user_id(uid):
            return "", False

        # Check users' locks
        if gid in glovar.user_ids[uid]["lock"]:
            return "", False

        # Proceed
        glovar.user_ids[uid]["lock"].add(gid)
        try:
            # Check ban status
            if gid in glovar.user_ids[uid]["ban"]:
                text += (f"{lang('user_id')}{lang('colon')}{mention_id(uid)}\n"
                         f"{lang('action')}{lang('colon')}{code(lang('action_kick'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_banned'))}\n"
                         f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
                return text, False

            # Forward evidence
            result = forward_evidence(
                client=client,
                message=message.reply_to_message,
                level=lang("action_kick")
            )

            # Check message
            if not result:
                text += (f"{lang('user_id')}{lang('colon')}{mention_id(uid)}\n"
                         f"{lang('action')}{lang('colon')}{code(lang('action_kick'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_deleted'))}\n"
                         f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
                return text, False

            # Count admin operation
            glovar.counts[gid][aid] += 1

            # Kick the user
            kick_user(client, gid, uid)
            glovar.user_ids[uid]["kick"].add(gid)
            update_score(client, uid)

            # Generate report text
            stored_link = general_link(result.message_id, message_link(result))
            text += (f"{lang('user_kicked')}{lang('colon')}{mention_id(uid)}\n"
                     f"{lang('stored_message')}{lang('colon')}{stored_link}\n"
                     f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")

            if reason:
                text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

            # Update success status
            success = True

            # Share
            ask_for_help(client, "delete", gid, uid)
            send_debug(
                client=client,
                message=message,
                action=lang("action_kick"),
                uid=uid,
                aid=aid,
                em=result,
                reason=reason
            )
        finally:
            glovar.user_ids[uid]["lock"].discard(gid)
    except Exception as e:
        logger.warning(f"Remove user error: {e}", exc_info=True)

    return text, success


def report_answer(client: Client, message: Message, gid: int, aid: int, mid: int,
                  action_type: str, key: str, reason: str = None) -> str:
    # Answer the user's report
    try:
        report_record = glovar.reports.get(key)

        if not report_record:
            message_text = get_text(message)
            uid = get_int(message_text.split("\n")[0].split(lang("colon"))[1])
            text = (f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n"
                    f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                    f"{lang('reason')}{lang('colon')}{code(lang('expired'))}\n")
            thread(edit_message_text, (client, gid, mid, text))
            delay(15, delete_message, [client, gid, mid])
            glovar.user_ids[uid]["waiting"].discard(gid)
            save("user_ids")
            return ""

        if not report_record["time"]:
            return ""

        rid = report_record["reporter_id"]
        uid = report_record["user_id"]
        r_mid = report_record["message_id"]
        record_reason = report_record["reason"]

        if not reason:
            reason = record_reason

        if not (init_user_id(rid) and init_user_id(uid)):
            return ""

        # Check users' locks
        if gid in glovar.user_ids[uid]["lock"] or gid in glovar.user_ids[rid]["lock"]:
            return lang("answer_proceeded")

        # Lock the report status
        glovar.reports[key]["time"] = 0
        try:
            if action_type == "ban":
                text, markup = ban_user(client, message, uid, aid, 0, reason)
                thread(delete_message, (client, gid, r_mid))
            elif action_type == "warn":
                text, markup = warn_user(client, message, uid, aid, reason)
                thread(delete_message, (client, gid, r_mid))
            elif action_type == "abuse":
                if not rid:
                    return ""

                message.reply_to_message.from_user.id = rid
                message.reply_to_message.from_user.is_self = lang("abuse_report")
                text, markup = warn_user(client, message, rid, aid)
                text += f"{lang('reason')}{lang('colon')}{code(lang('reason_abuse'))}\n"
            else:
                reported_link = general_link(r_mid, f'{get_channel_link(message)}/{r_mid}')

                if rid:
                    reporter_text = code(rid)
                else:
                    reporter_text = code(lang("auto_triggered"))

                text = (f"{lang('reported_user')}{lang('colon')}{mention_id(uid)}\n"
                        f"{lang('reported_message')}{lang('colon')}{reported_link}\n"
                        f"{lang('reporter')}{lang('colon')}{reporter_text}\n"
                        f"{lang('action')}{lang('colon')}{code(lang('action_cancel'))}\n"
                        f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                        f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
                markup = None

            if markup:
                secs = 180
            else:
                secs = 15

            thread(edit_message_text, (client, gid, mid, text, markup))
            delay(secs, delete_message, [client, gid, mid])
        finally:
            glovar.user_ids[uid]["lock"].discard(gid)
            glovar.user_ids[rid]["lock"].discard(gid)
            glovar.user_ids[uid]["waiting"].discard(gid)
            glovar.user_ids[rid]["waiting"].discard(gid)
            save("user_ids")
    except Exception as e:
        logger.warning(f"Report answer error: {e}", exc_info=True)

    return ""


def report_user(gid: int, user: User, rid: int, mid: int, reason: str = None) -> (str, InlineKeyboardMarkup, str):
    # Report a user
    text = ""
    markup = None
    key = ""
    try:
        if user:
            uid = user.id
        else:
            return "", None

        glovar.user_ids[uid]["waiting"].add(gid)
        glovar.user_ids[rid]["waiting"].add(gid)
        save("user_ids")

        key = random_str(8)

        while glovar.reports.get(key):
            key = random_str(8)

        glovar.reports[key] = {
            "time": get_now(),
            "group_id": gid,
            "reporter_id": rid,
            "user_id": uid,
            "message_id": mid,
            "report_id": 0,
            "reason": reason
        }

        if rid:
            reporter_text = code("██████")
        else:
            reporter_text = code(lang("auto_triggered"))

        text = (f"{lang('reported_user')}{lang('colon')}{mention_id(uid)}\n"
                f"{lang('reported_message')}{lang('colon')}{general_link(mid, f'{get_channel_link(gid)}/{mid}')}\n"
                f"{lang('reporter')}{lang('colon')}{reporter_text}\n"
                f"{lang('mention_admins')}{lang('colon')}{get_admin_text(gid)}\n"
                f"{lang('description')}{lang('colon')}{code(lang('description_wait_admin'))}\n")

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        warn_data = button_data("report", "warn", key)
        ban_data = button_data("report", "ban", key)
        cancel_data = button_data("report", "cancel", key)
        markup_list = [
            [
                InlineKeyboardButton(
                    text=lang("warn"),
                    callback_data=warn_data
                ),
                InlineKeyboardButton(
                    text=lang("ban"),
                    callback_data=ban_data
                )
            ],
            [
                InlineKeyboardButton(
                    text=lang("cancel"),
                    callback_data=cancel_data
                )
            ]
        ]

        if rid:
            abuse_data = button_data("report", "abuse", key)
            markup_list[1].append(
                InlineKeyboardButton(
                    text=lang("abuse"),
                    callback_data=abuse_data
                )
            )

        markup = InlineKeyboardMarkup(markup_list)
    except Exception as e:
        logger.warning(f"Report user error: {e}", exc_info=True)

    return text, markup, key


def warn_user(client: Client, message: Message, uid: int, aid: int,
              reason: str = None) -> (str, InlineKeyboardMarkup):
    # Warn a user
    text = ""
    markup = None
    try:
        # Basic data
        gid = message.chat.id

        # Init user data
        if not init_user_id(uid):
            return "", None

        # Check users' locks
        if gid in glovar.user_ids[uid]["lock"]:
            return "", None

        # Proceed
        glovar.user_ids[uid]["lock"].add(gid)
        try:
            # Check ban status
            if gid in glovar.user_ids[uid]["ban"]:
                text += (f"{lang('user_id')}{lang('colon')}{mention_id(uid)}\n"
                         f"{lang('action')}{lang('colon')}{code(lang('action_warn'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_banned'))}\n"
                         f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
                return text, None

            # Forward evidence
            result = forward_evidence(
                client=client,
                message=message.reply_to_message,
                level=lang("action_warn")
            )

            # Check message
            if not result:
                text += (f"{lang('user_id')}{lang('colon')}{mention_id(uid)}\n"
                         f"{lang('action')}{lang('colon')}{code(lang('action_warn'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_deleted'))}\n"
                         f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
                return text, None

            # Add warn count
            if not glovar.user_ids[uid]["warn"].get(gid, 0):
                glovar.user_ids[uid]["warn"][gid] = 1
                update_score(client, uid)
            else:
                glovar.user_ids[uid]["warn"][gid] += 1

            # Read count and group config
            warn_count = glovar.user_ids[uid]["warn"][gid]
            limit = glovar.configs[gid]["limit"]

            # Warn or ban
            if warn_count >= limit:
                glovar.user_ids[uid]["lock"].discard(gid)
                text = (f"{lang('user_banned')}{lang('colon')}{mention_id(uid)}\n"
                        f"{lang('ban_reason')}{lang('colon')}{code(lang('reason_limit'))}\n")
                _, markup = ban_user(client, message, uid, aid, result, reason)
            else:
                text = (f"{lang('user_warned')}{lang('colon')}{mention_id(uid)}\n"
                        f"{lang('user_warns')}{lang('colon')}{code(f'{warn_count}/{limit}')}\n")

                data = button_data("undo", "warn", uid)
                markup = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text=lang("undo"),
                                callback_data=data
                            )
                        ]
                    ]
                )

                send_debug(
                    client=client,
                    message=message,
                    action=lang("action_warn"),
                    uid=uid,
                    aid=aid,
                    em=result,
                    reason=reason
                )

            stored_link = general_link(result.message_id, message_link(result))
            text += (f"{lang('stored_message')}{lang('colon')}{stored_link}\n"
                     f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")

            if markup and reason:
                text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"
        finally:
            glovar.user_ids[uid]["lock"].discard(gid)
    except Exception as e:
        logger.warning(f"Warn user error: {e}", exc_info=True)

    return text, markup


def unban_user(client: Client, message: Message, uid: int, aid: int) -> str:
    # Unban a user
    text = ""
    try:
        # Basic data
        gid = message.chat.id

        # Check ban status
        if gid not in glovar.user_ids[uid]["ban"]:
            text = (f"{lang('user_id')}{lang('colon')}{mention_id(uid)}\n"
                    f"{lang('action')}{lang('colon')}{code(lang('action_unban'))}\n"
                    f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                    f"{lang('reason')}{lang('colon')}{code(lang('reason_none'))}\n"
                    f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
            return text

        # Proceed
        unban_chat_member(client, gid, uid)
        glovar.user_ids[uid]["ban"].discard(gid)
        update_score(client, uid)
        text = (f"{lang('user_unbanned')}{lang('colon')}{code(uid)}\n"
                f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
        send_debug(
            client=client,
            message=message,
            action=lang("action_unban"),
            uid=uid,
            aid=aid
        )
    except Exception as e:
        logger.warning(f"Unban user error: {e}", exc_info=True)

    return text


def undo_user(client: Client, message: Message, aid: int, uid: int, action_type: str) -> str:
    try:
        # Basic
        gid = message.chat.id
        mid = message.message_id

        # Init user data
        if not init_user_id(uid):
            return ""

        # Check the user's lock
        if gid in glovar.user_ids[uid]["lock"]:
            return lang("answer_proceeded")

        # Proceed
        glovar.user_ids[uid]["lock"].add(gid)
        try:
            if action_type == "ban":
                text = unban_user(client, message, uid, aid)
            else:
                text = unwarn_user(client, message, uid, aid)

            thread(edit_message_text, (client, gid, mid, text))
        finally:
            glovar.user_ids[uid]["lock"].discard(gid)

        # Save data
        save("user_ids")
    except Exception as e:
        logger.warning(f"Undo user error: {e}", exc_info=True)

    return ""


def unwarn_user(client: Client, message: Message, uid: int, aid: int) -> str:
    # Unwarn a user
    text = ""
    try:
        # Basic data
        gid = message.chat.id

        # Check ban status
        if gid in glovar.user_ids[uid]["ban"]:
            text = (f"{lang('user_id')}{lang('colon')}{mention_id(uid)}\n"
                    f"{lang('action')}{lang('colon')}{code(lang('action_unwarn'))}\n"
                    f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                    f"{lang('reason')}{lang('colon')}{code(lang('reason_banned'))}\n"
                    f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
            return text

        # Check warnings count
        if not glovar.user_ids[uid]["warn"].get(gid, 0):
            text = (f"{lang('user_id')}{lang('colon')}{mention_id(uid)}\n"
                    f"{lang('action')}{lang('colon')}{lang('action_unwarn')}\n"
                    f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                    f"{lang('reason')}{lang('colon')}{code(lang('reason_none'))}\n"
                    f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n")
            return text

        # Proceed
        glovar.user_ids[uid]["warn"][gid] -= 1
        warn_count = glovar.user_ids[uid]["warn"][gid]

        if warn_count == 0:
            glovar.user_ids[uid]["warn"].pop(gid, 0)
            update_score(client, uid)
            text = (f"{lang('user_unwarned')}{lang('colon')}{mention_id(uid)}\n"
                    f"{lang('user_warns')}{lang('colon')}{code(lang('reason_none'))}\n")
            send_debug(
                client=client,
                message=message,
                action=lang("action_unwarns"),
                uid=uid,
                aid=aid
            )
        else:
            limit = glovar.configs[gid]["limit"]
            text = (f"{lang('user_unwarned')}{lang('colon')}{mention_id(uid)}\n"
                    f"{lang('user_warns')}{lang('colon')}{code(f'{warn_count}/{limit}')}\n")

        text += f"{lang('description')}{lang('colon')}{code(lang('description_by_admin'))}\n"
    except Exception as e:
        logger.warning(f"Unwarn user error: {e}", exc_info=True)

    return text
