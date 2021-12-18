#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from random import randint

from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, idle

from plugins import glovar
from plugins.functions.etc import delay
from plugins.functions.timers import (backup_files, interval_hour_01, reset_data, update_admins, update_report_ids,
                                      update_status)

# Enable logging
logger = logging.getLogger(__name__)

# Config session
app = Client(
    session_name="bot",
    bot_token=glovar.bot_token
)
app.start()

# Send online status
delay(3, update_status, [app, "online"])

# Timer
scheduler = BackgroundScheduler(job_defaults={"misfire_grace_time": 60})
scheduler.add_job(interval_hour_01, "interval", [app], hours=1)
scheduler.add_job(update_status, "cron", [app, "awake"], minute=randint(30, 34), second=randint(0, 59))
scheduler.add_job(backup_files, "cron", [app], hour=20)
scheduler.add_job(update_report_ids, "cron", [app], hour=21, minute=30)
scheduler.add_job(reset_data, "cron", [app], day=glovar.date_reset, hour=22)
scheduler.add_job(update_admins, "cron", [app], hour=22, minute=30)
scheduler.start()

# Hold
idle()

# Stop
app.stop()
