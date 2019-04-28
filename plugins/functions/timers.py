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
from time import sleep

from pyrogram import Client

from .. import glovar
from .etc import code, general_link, send_data, thread
from .file import crypt_file, save
from .telegram import get_admins, get_group_info, send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def backup_files(client: Client) -> bool:
    try:
        for file in glovar.file_list:
            try:
                exchange_text = send_data(
                    sender="WARN",
                    receivers=["BACKUP"],
                    action="backup",
                    action_type="pickle",
                    data=file
                )
                crypt_file("encrypt", f"data/{file}", f"tmp/{file}")
                thread(send_document, (client, glovar.exchange_channel_id, f"tmp/{file}", exchange_text))
                sleep(5)
            except Exception as e:
                logger.warning(f"Send backup file {file} error: {e}", exc_info=True)

        return True
    except Exception as e:
        logger.warning(f"Backup error: {e}", exc_info=True)

    return False


def reset_data() -> bool:
    glovar.user_ids = {}
    save("user_ids")

    return True


def update_admins(client: Client) -> bool:
    group_list = list(glovar.configs)
    for gid in group_list:
        try:
            should_leave = True
            reason_text = "permissions"
            admin_members = get_admins(client, gid)
            if admin_members:
                glovar.admin_ids[gid] = {admin.user.id for admin in admin_members if not admin.user.is_bot}
                if glovar.user_id not in glovar.admin_ids[gid]:
                    reason_text = "user"
                else:
                    for admin in admin_members:
                        if admin.user.is_self:
                            if not (admin.permissions.can_delete_messages and admin.permissions.can_restrict_members):
                                should_leave = False

                if should_leave:
                    group_name, group_link = get_group_info(client, gid)
                    exchange_text = send_data(
                        sender="WARN",
                        receivers=["MANAGE"],
                        action="request",
                        action_type="leave",
                        data={
                            "group_id": gid,
                            "group_name": group_name,
                            "group_link": group_link,
                            "reason": reason_text
                        }
                    )
                    thread(send_message, (client, glovar.exchange_channel_id, exchange_text))
                    if reason_text == "user":
                        reason_text = f"缺失 {glovar.user_name}"
                    elif reason_text == "permissions":
                        reason_text = f"权限缺失"

                    debug_text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                                  f"群组名称：{general_link(group_name, group_link)}\n"
                                  f"群组 ID：{code(gid)}\n"
                                  f"状态：{code(reason_text)}")
                    thread(send_message, (client, glovar.debug_channel_id, debug_text))
        except Exception as e:
            logger.warning(f"Update admin in {gid} error: {e}")

    return True


def update_status(client: Client) -> bool:
    try:
        exchange_text = send_data(
            sender="WARN",
            receivers=["MANAGE"],
            action="update",
            action_type="status",
            data="awake"
        )
        thread(send_message, (client, glovar.exchange_channel_id, exchange_text))
        return True
    except Exception as e:
        logger.warning(f"Update status error: {e}")

    return False
