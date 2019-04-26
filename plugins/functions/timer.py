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
from .etc import send_data, thread
from .files import crypt_file
from .telegram import send_document

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
