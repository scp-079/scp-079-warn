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

from .. import glovar
from .files import save

# Enable logging
logger = logging.getLogger(__name__)


def init_group_id(gid: int) -> bool:
    try:
        if glovar.modes.get(gid) is None:
            glovar.modes[gid] = {
                "limit": 3,
                "locked": False,
                "mention": False,
                "report": {
                    "auto": False,
                    "manual": False
                }
            }
            save("modes")

        if glovar.admin_ids.get(gid) is None:
            glovar.admin_ids[gid] = set()
            save("admin_ids")

        return True
    except Exception as e:
        logger.warning(f"Init group id {gid} error: {e}", exc_info=True)

    return False


def init_user_id(uid: int) -> bool:
    try:
        if glovar.user_ids.get(uid) is None:
            glovar.user_ids[uid] = {
                "ban": set(),
                "locked": set(),
                "score": 0,
                "warn": {},
                "waiting": set()
            }
            save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Init user id {uid} error: {e}", exc_info=True)

    return False
