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
import pickle
from copy import deepcopy
from json import loads
from typing import Any

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from .channel import get_debug_text, share_data
from .etc import code, general_link, get_text, lang, mention_id, thread
from .file import crypt_file, data_to_file, delete_file, get_downloaded_path, get_new_path, save
from .filters import is_declared_message_id
from .group import get_config_text, get_message, leave_group
from .ids import init_group_id, init_user_id
from .telegram import send_message, send_report_message
from .timers import update_admins
from .user import report_user

# Enable logging
logger = logging.getLogger(__name__)


def receive_add_bad(data: dict) -> bool:
    # Receive bad users or channels that other bots shared
    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Receive bad user
        if the_type == "user":
            glovar.bad_ids["users"].add(the_id)

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive add bad error: {e}", exc_info=True)

    return False


def receive_config_commit(data: dict) -> bool:
    # Receive config commit
    try:
        # Basic data
        gid = data["group_id"]
        config = data["config"]

        glovar.configs[gid] = config
        save("configs")

        return True
    except Exception as e:
        logger.warning(f"Receive config commit error: {e}", exc_info=True)

    return False


def receive_config_reply(client: Client, data: dict) -> bool:
    # Receive config reply
    try:
        # Basic data
        gid = data["group_id"]
        uid = data["user_id"]
        link = data["config_link"]

        text = (f"{lang('admin')}{lang('colon')}{code(uid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('config_change'))}\n"
                f"{lang('description')}{lang('colon')}{code(lang('config_button'))}\n")
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=lang("config_go"),
                        url=link
                    )
                ]
            ]
        )
        thread(send_report_message, (180, client, gid, text, None, markup))

        return True
    except Exception as e:
        logger.warning(f"Receive config reply error: {e}", exc_info=True)

    return False


def receive_config_show(client: Client, data: dict) -> bool:
    # Receive config show request
    try:
        # Basic Data
        aid = data["admin_id"]
        mid = data["message_id"]
        gid = data["group_id"]

        # Generate report message's text
        result = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                  f"{lang('action')}{lang('colon')}{code(lang('config_show'))}\n"
                  f"{lang('group_id')}{lang('colon')}{code(gid)}\n")

        if glovar.configs.get(gid, {}):
            result += get_config_text(glovar.configs[gid])
        else:
            result += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                       f"{lang('reason')}{lang('colon')}{code(lang('reason_none'))}\n")

        # Send the text data
        file = data_to_file(result)
        share_data(
            client=client,
            receivers=["MANAGE"],
            action="config",
            action_type="show",
            data={
                "admin_id": aid,
                "message_id": mid,
                "group_id": gid
            },
            file=file
        )

        return True
    except Exception as e:
        logger.warning(f"Receive config show error: {e}", exc_info=True)

    return False


def receive_declared_message(data: dict) -> bool:
    # Update declared message's id
    try:
        # Basic data
        gid = data["group_id"]
        mid = data["message_id"]

        if not glovar.admin_ids.get(gid):
            return True

        if init_group_id(gid):
            glovar.declared_message_ids[gid].add(mid)

        return True
    except Exception as e:
        logger.warning(f"Receive declared message error: {e}", exc_info=True)

    return False


def receive_file_data(client: Client, message: Message, decrypt: bool = True) -> Any:
    # Receive file's data from exchange channel
    data = None
    try:
        if not message.document:
            return None

        file_id = message.document.file_id
        file_ref = message.document.file_ref
        path = get_downloaded_path(client, file_id, file_ref)

        if not path:
            return None

        if decrypt:
            # Decrypt the file, save to the tmp directory
            path_decrypted = get_new_path()
            crypt_file("decrypt", path, path_decrypted)
            path_final = path_decrypted
        else:
            # Read the file directly
            path_decrypted = ""
            path_final = path

        with open(path_final, "rb") as f:
            data = pickle.load(f)

        for f in {path, path_decrypted}:
            thread(delete_file, (f,))
    except Exception as e:
        logger.warning(f"Receive file error: {e}", exc_info=True)

    return data


def receive_help_report(client: Client, data: dict) -> bool:
    # Receive help report requests
    try:
        # Basic data
        gid = data["group_id"]
        uid = data["user_id"]
        mid = data["message_id"]

        # Check declared status
        if is_declared_message_id(gid, mid):
            return True

        # Check group
        if gid not in glovar.admin_ids:
            return True

        if not init_group_id(gid):
            return True

        if not glovar.configs[gid]["report"]["auto"]:
            return True

        if not (init_user_id(0) and init_user_id(uid)
                and gid not in glovar.user_ids[uid]["lock"]
                and gid not in glovar.user_ids[uid]["waiting"]
                and gid not in glovar.user_ids[uid]["ban"]):
            return True

        the_message = get_message(client, gid, mid)

        if not the_message:
            return True

        text, markup, key = report_user(gid, the_message.from_user, 0, mid)
        result = send_message(client, gid, text, mid, markup)

        if result:
            glovar.reports[key]["report_id"] = result.message_id
        else:
            glovar.reports[key].pop(key, {})

        save("reports")

        return True
    except Exception as e:
        logger.warning(f"Receive help report error: {e}", exc_info=True)

    return False


def receive_leave_approve(client: Client, data: dict) -> bool:
    # Receive leave approve
    try:
        # Basic data
        admin_id = data["admin_id"]
        the_id = data["group_id"]
        reason = data["reason"]

        if reason in {"permissions", "user"}:
            reason = lang(f"reason_{reason}")

        if not glovar.admin_ids.get(the_id):
            return True

        text = get_debug_text(client, the_id)
        text += (f"{lang('admin_project')}{lang('colon')}{mention_id(admin_id)}\n"
                 f"{lang('status')}{lang('colon')}{code(lang('leave_approve'))}\n")

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        leave_group(client, the_id)
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Receive leave approve error: {e}", exc_info=True)

    return False


def receive_refresh(client: Client, data: int) -> bool:
    # Receive refresh
    try:
        # Basic data
        aid = data

        # Update admins
        update_admins(client)

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('refresh'))}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Receive refresh error: {e}", exc_info=True)

    return False


def receive_remove_bad(data: dict) -> bool:
    # Receive removed bad objects
    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Remove bad user
        if the_type == "user":
            glovar.bad_ids["users"].discard(the_id)
            glovar.user_ids[the_id] = deepcopy(glovar.default_user_status)
            save("user_ids")

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove bad error: {e}", exc_info=True)

    return False


def receive_rollback(client: Client, message: Message, data: dict) -> bool:
    # Receive rollback data
    try:
        # Basic data
        aid = data["admin_id"]
        the_type = data["type"]
        the_data = receive_file_data(client, message)

        if not the_data:
            return True

        exec(f"glovar.{the_type} = the_data")
        save(the_type)

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('rollback'))}\n"
                f"{lang('more')}{lang('colon')}{code(the_type)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Receive rollback error: {e}", exc_info=True)

    return False


def receive_text_data(message: Message) -> dict:
    # Receive text's data from exchange channel
    data = {}
    try:
        text = get_text(message)

        if not text:
            return {}

        data = loads(text)
    except Exception as e:
        logger.warning(f"Receive text data error: {e}")

    return data
