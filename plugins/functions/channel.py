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
from json import dumps
from typing import List, Optional, Union

from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.types import Chat, Message

from plugins import glovar
from plugins.functions.etc import (code, code_block, general_link, get_full_name, get_command_type, lang, message_link,
                                   thread, wait_flood)
from plugins.functions.file import crypt_file, delete_file, get_new_path, save
from plugins.functions.telegram import get_group_info, get_user_bio, send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def ask_for_help(client: Client, level: str, gid: int, uid: int, group: str = "single") -> bool:
    # Let USER help to delete all message from user, or ban user globally
    try:
        data = {
            "group_id": gid,
            "user_id": uid
        }

        if level == "ban":
            data["type"] = (glovar.configs[gid].get("restrict") and "restrict") or "ban"
        elif level == "delete":
            data["type"] = group

        data["delete"] = glovar.configs[gid].get("delete")

        share_data(
            client=client,
            receivers=["USER"],
            action="help",
            action_type=level,
            data=data
        )

        return True
    except Exception as e:
        logger.warning(f"Ask for help error: {e}", exc_info=True)

    return False


def exchange_to_hide(client: Client) -> bool:
    # Let other bots exchange data in the hide channel instead
    try:
        glovar.should_hide = True
        share_data(
            client=client,
            receivers=["EMERGENCY"],
            action="backup",
            action_type="hide",
            data=True
        )

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('issue')}{lang('colon')}{code(lang('exchange_invalid'))}\n"
                f"{lang('auto_fix')}{lang('colon')}{code(lang('protocol_1'))}\n")
        thread(send_message, (client, glovar.critical_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange to hide error: {e}", exc_info=True)

    return False


def format_data(sender: str, receivers: List[str], action: str, action_type: str,
                data: Union[bool, dict, int, str] = None) -> str:
    # See https://scp-079.org/exchange/
    text = ""
    try:
        data = {
            "from": sender,
            "to": receivers,
            "action": action,
            "type": action_type,
            "data": data
        }
        text = code_block(dumps(data, indent=4))
    except Exception as e:
        logger.warning(f"Format data error: {e}", exc_info=True)

    return text


def forward_evidence(client: Client, message: Message, level: str,
                     more: str = None) -> Optional[Union[bool, Message]]:
    # Forward the message to logging channel as evidence
    result = None
    try:
        if not message or not message.from_user:
            return result

        # Basic information
        uid = message.from_user.id
        text = (f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('user_id')}{lang('colon')}{code(uid)}\n"
                f"{lang('level')}{lang('colon')}{code(level)}\n"
                f"{lang('rule')}{lang('colon')}{code(lang('rule_admin'))}\n")

        # Additional information
        if message.game:
            text += f"{lang('message_type')}{lang('colon')}{code(lang('gam'))}\n"
        elif message.service:
            text += f"{lang('message_type')}{lang('colon')}{code(lang('ser'))}\n"

        if message.game:
            text += f"{lang('message_game')}{lang('colon')}{code(message.game.short_name)}\n"

        if message.from_user.is_self:
            if message.from_user.is_self is True:
                if message.entities:
                    for en in message.entities:
                        if not en.user:
                            continue

                        name = get_full_name(en.user)
                        if not name:
                            continue

                        text += f"{lang('user_name')}{lang('colon')}{code(name)}\n"
                        break

                text += f"{lang('more')}{lang('colon')}{code(lang('from_self'))}\n"
            # User didn't use report function wisely, should not forward evidence
            else:
                text += f"{lang('more')}{lang('colon')}{code(message.from_user.is_self)}"

            result = send_message(client, glovar.warn_channel_id, text)
            return result

        name = get_full_name(message.from_user)
        if name:
            text += f"{lang('user_name')}{lang('colon')}{code(name)}\n"

        if message.service and level == lang("action_ban"):
            bio = get_user_bio(client, uid)
            if bio:
                text += f"{lang('user_bio')}{lang('colon')}{code(bio)}\n"

        # Extra information
        if message.contact or message.location or message.venue or message.video_note or message.voice:
            text += f"{lang('more')}{lang('colon')}{code(lang('privacy'))}\n"
        elif message.game or message.service:
            text += f"{lang('more')}{lang('colon')}{code(lang('cannot_forward'))}\n"
        elif more:
            text += f"{lang('more')}{lang('colon')}{code(more)}\n"

        # DO NOT try to forward these types of message
        if (message.contact
                or message.location
                or message.venue
                or message.video_note
                or message.voice
                or message.game
                or message.service):
            result = send_message(client, glovar.warn_channel_id, text)
            return result

        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = message.forward(
                    chat_id=glovar.warn_channel_id,
                    disable_notification=True
                )
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except Exception as e:
                logger.info(f"Forward evidence message error: {e}", exc_info=True)
                return False

        result = result.message_id
        result = send_message(client, glovar.warn_channel_id, text, result)
    except Exception as e:
        logger.warning(f"Forward evidence error: {e}", exc_info=True)

    return result


def get_debug_text(client: Client, context: Union[int, Chat, List[int]]) -> str:
    # Get a debug message text prefix
    text = ""
    try:
        # Prefix
        text = f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"

        # List of group ids
        if isinstance(context, list):
            for group_id in context:
                group_name, group_link = get_group_info(client, group_id)
                text += (f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                         f"{lang('group_id')}{lang('colon')}{code(group_id)}\n")

        # One group
        else:
            # Get group id
            if isinstance(context, int):
                group_id = context
            else:
                group_id = context.id

            # Generate the group info text
            group_name, group_link = get_group_info(client, context)
            text += (f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                     f"{lang('group_id')}{lang('colon')}{code(group_id)}\n")
    except Exception as e:
        logger.warning(f"Get debug text error: {e}", exc_info=True)

    return text


def send_debug(client: Client, message: Message, action: str, uid: int, aid: int, em: Message = None,
               reason: str = None) -> bool:
    # Send the debug message
    try:
        text = get_debug_text(client, message.chat)
        text += (f"{lang('user_id')}{lang('colon')}{code(uid)}\n"
                 f"{lang('action')}{lang('colon')}{code(action)}\n"
                 f"{lang('admin_group')}{lang('colon')}{code(aid)}\n")

        if em:
            text += f"{lang('stored_message')}{lang('colon')}{general_link(em.message_id, message_link(em))}\n"

        # If the message is a report callback message
        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"
        elif message.from_user.is_self and action not in {lang("action_unban"), lang("action_unwarns")}:
            text += f"{lang('reason')}{lang('colon')}{code(lang('by_button'))}\n"
        else:
            reason = get_command_type(message)
            if reason:
                text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Send debug error: {e}", exc_info=True)

    return False


def share_data(client: Client, receivers: List[str], action: str, action_type: str,
               data: Union[bool, dict, int, str] = None, file: str = None, encrypt: bool = True) -> bool:
    # Use this function to share data in the channel
    try:
        thread(
            target=share_data_thread,
            args=(client, receivers, action, action_type, data, file, encrypt)
        )

        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False


def share_data_thread(client: Client, receivers: List[str], action: str, action_type: str,
                      data: Union[bool, dict, int, str] = None, file: str = None, encrypt: bool = True) -> bool:
    # Share data thread
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if not receivers:
            return True

        if glovar.should_hide:
            channel_id = glovar.hide_channel_id
        else:
            channel_id = glovar.exchange_channel_id

        if file:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )

            if encrypt:
                # Encrypt the file, save to the tmp directory
                file_path = get_new_path()
                crypt_file("encrypt", file, file_path)
            else:
                # Send directly
                file_path = file

            result = send_document(client, channel_id, file_path, text)

            # Delete the tmp file
            if result:
                for f in {file, file_path}:
                    f.startswith("tmp/") and thread(delete_file, (f,))
        else:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            result = send_message(client, channel_id, text)

        # Sending failed due to channel issue
        if result is False and not glovar.should_hide:
            # Use hide channel instead
            exchange_to_hide(client)
            thread(share_data, (client, receivers, action, action_type, data, file, encrypt))

        return True
    except Exception as e:
        logger.warning(f"Share data thread error: {e}", exc_info=True)

    return False


def update_score(client: Client, uid: int) -> bool:
    # Update a user's score, share it
    try:
        ban_count = len(glovar.user_ids[uid]["ban"])
        kick_count = len(glovar.user_ids[uid]["kick"])
        warn_count = len(glovar.user_ids[uid]["warn"])
        score = ban_count * 1 + kick_count * 0.3 + warn_count * 0.4
        glovar.user_ids[uid]["score"][glovar.sender.lower()] = score
        save("user_ids")
        share_data(
            client=client,
            receivers=glovar.receivers["score"],
            action="update",
            action_type="score",
            data={
                "id": uid,
                "score": round(score, 1)
            }
        )

        return True
    except Exception as e:
        logger.warning(f"Update score error: {e}", exc_info=True)

    return False
