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
from pickle import dump
from shutil import copyfile

from pyAesCrypt import decryptFile, encryptFile

from .. import glovar
from .etc import thread

# Enable logging
logger = logging.getLogger(__name__)


def crypt_file(operation: str, file_in: str, file_out: str) -> bool:
    # Encrypt or decrypt a file
    try:
        buffer = 64 * 1024
        if operation == "decrypt":
            decryptFile(file_in, file_out, glovar.password, buffer)
        else:
            encryptFile(file_in, file_out, glovar.password, buffer)

        return True
    except Exception as e:
        logger.warning(f"Crypt file error: {e}", exc_info=True)

    return False


def save(file: str) -> bool:
    # Save a global variable to a file
    try:
        thread(save_thread, (file,))
        return True
    except Exception as e:
        logger.warning(f"Save error: {e}", exc_info=True)

    return False


def save_thread(file: str) -> bool:
    # Save function's thread
    try:
        if glovar:
            with open(f"data/.{file}", "wb") as f:
                dump(eval(f"glovar.{file}"), f)

            copyfile(f"data/.{file}", f"data/{file}")

        return True
    except Exception as e:
        logger.error(f"Save data error: {e}", exc_info=True)

    return False
