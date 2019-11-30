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

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import get_debug_text, update_score
from ..functions.etc import code, delay, general_link, lang, mention_id, thread
from ..functions.file import save
from ..functions.filters import authorized_group, exchange_channel, from_user, hide_channel, new_group, test_group
from ..functions.group import leave_group
from ..functions.ids import init_group_id
from ..functions.receive import receive_add_bad, receive_clear_data, receive_config_commit, receive_config_reply
from ..functions.receive import receive_declared_message, receive_help_report, receive_leave_approve, receive_refresh
from ..functions.receive import receive_remove_bad, receive_remove_score, receive_remove_watch, receive_rollback
from ..functions.receive import receive_text_data, receive_user_score, receive_watch_user
from ..functions.telegram import get_admins, send_message
from ..functions.timers import backup_files

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & Filters.new_chat_members
                   & ~test_group & ~new_group & authorized_group
                   & from_user)
def check_join(client: Client, message: Message) -> bool:
    # Check new joined user
    glovar.locks["message"].acquire()
    try:
        # Basic data
        gid = message.chat.id

        for new in message.new_chat_members:
            # Basic data
            uid = new.id

            if not glovar.user_ids.get(uid, {}):
                continue

            if gid not in glovar.user_ids[uid]["ban"] and gid not in glovar.user_ids[uid]["kick"]:
                continue

            glovar.user_ids[uid]["ban"].discard(gid)
            glovar.user_ids[uid]["kick"].discard(gid)
            save("user_ids")
            update_score(client, uid)

        return True
    except Exception as e:
        logger.warning(f"Check join error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


@Client.on_message(Filters.incoming & Filters.channel & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & hide_channel, group=-1)
def exchange_emergency(client: Client, message: Message) -> bool:
    # Sent emergency channel transfer request
    try:
        # Read basic information
        data = receive_text_data(message)

        if not data:
            return True

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]

        if "EMERGENCY" not in receivers:
            return True

        if action != "backup":
            return True

        if action_type != "hide":
            return True

        if data is True:
            glovar.should_hide = data
        elif data is False and sender == "MANAGE":
            glovar.should_hide = data

        project_text = general_link(glovar.project_name, glovar.project_link)
        hide_text = (lambda x: lang("enabled") if x else "disabled")(glovar.should_hide)
        text = (f"{lang('project')}{lang('colon')}{project_text}\n"
                f"{lang('action')}{lang('colon')}{code(lang('transfer_channel'))}\n"
                f"{lang('emergency_channel')}{lang('colon')}{code(hide_text)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & (Filters.new_chat_members | Filters.group_chat_created | Filters.supergroup_chat_created)
                   & ~test_group & new_group
                   & from_user)
def init_group(client: Client, message: Message) -> bool:
    # Initiate new groups
    try:
        gid = message.chat.id
        text = get_debug_text(client, message.chat)
        invited_by = message.from_user.id

        # Check permission
        if invited_by == glovar.user_id:
            # Remove the left status
            if gid in glovar.left_group_ids:
                glovar.left_group_ids.discard(gid)
                save("left_group_ids")

            # Update group's admin list
            if not init_group_id(gid):
                return True

            admin_members = get_admins(client, gid)
            if admin_members:
                glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                         if not admin.user.is_bot and not admin.user.is_deleted}
                save("admin_ids")
                text += f"{lang('status')}{lang('colon')}{code(lang('status_joined'))}\n"
            else:
                thread(leave_group, (client, gid))
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_left'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_admin'))}\n")
        else:
            if gid in glovar.left_group_ids:
                return leave_group(client, gid)

            leave_group(client, gid)
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_left'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('reason_unauthorized'))}\n")
            if message.from_user.username:
                text += f"{lang('inviter')}{lang('colon')}{mention_id(invited_by)}\n"
            else:
                text += f"{lang('inviter')}{lang('colon')}{code(invited_by)}\n"

        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Init group error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.channel & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & exchange_channel)
def process_data(client: Client, message: Message) -> bool:
    # Process the data in exchange channel
    glovar.locks["receive"].acquire()
    try:
        data = receive_text_data(message)

        if not data:
            return True

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]

        # This will look awkward,
        # seems like it can be simplified,
        # but this is to ensure that the permissions are clear,
        # so it is intentionally written like this
        if glovar.sender in receivers:

            if sender == "CAPTCHA":

                if action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "CLEAN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "CONFIG":

                if action == "config":
                    if action_type == "commit":
                        receive_config_commit(data)
                    elif action_type == "reply":
                        receive_config_reply(client, data)

            elif sender == "LANG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "LONG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "MANAGE":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)

                elif action == "backup":
                    if action_type == "now":
                        thread(backup_files, (client,))
                    elif action_type == "rollback":
                        receive_rollback(client, message, data)

                elif action == "clear":
                    receive_clear_data(client, action_type, data)

                elif action == "leave":
                    if action_type == "approve":
                        receive_leave_approve(client, data)

                elif action == "remove":
                    if action_type == "bad":
                        receive_remove_bad(data)
                    elif action_type == "score":
                        receive_remove_score(data)
                    elif action_type == "watch":
                        receive_remove_watch(data)

                elif action == "update":
                    if action_type == "refresh":
                        receive_refresh(client, data)

            elif sender == "NOFLOOD":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOPORN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOSPAM":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)

                elif action == "help":
                    if action_type == "report":
                        delay(10, receive_help_report, [client, data])
                
                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)
            
            elif sender == "RECHECK":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)
            
            elif sender == "WATCH":

                if action == "add":
                    if action_type == "watch":
                        receive_watch_user(data)

        return True
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)
    finally:
        glovar.locks["receive"].release()

    return False
