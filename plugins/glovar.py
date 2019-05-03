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
from configparser import RawConfigParser
from os import mkdir
from os.path import exists
from shutil import rmtree
from typing import Dict, List, Set, Union

# Enable logging
logger = logging.getLogger(__name__)

# Init
all_commands: List[str] = [
    "admin",
    "admins",
    "ban",
    "config",
    "forgive",
    "report",
    "version",
    "warn",
    "warn_config"
]

default_config: Dict[str, Union[bool, int, Dict[str, bool]]] = {
    "default": True,
    "limit": 3,
    "locked": 0,
    "mention": False,
    "report": {
        "auto": False,
        "manual": False
    }
}

default_user_status: Dict[str, Union[float, Dict[int, int], Set[int]]] = {
    "ban": set(),
    "locked": set(),
    "score": 0,
    "warn": {},
    "waiting": set()
}

left_group_ids: Set[int] = set()

message_ids: Dict[int, int] = {}
# message_ids = {
#     -10012345678: 123
# }

report_records: Dict[str, Dict[str, int]] = {}
# report_records = {
#     "random": {
#         "r": 12345678,
#         "u": 12345679
#     }
# }

version: str = "0.1.6"

# Load data from pickle

# Init dir
try:
    rmtree("tmp")
except Exception as e:
    logger.info(f"Remove tmp error: {e}")

for path in ["data", "tmp"]:
    if not exists(path):
        mkdir(path)

# Init ids variables

admin_ids: Dict[int, Set[int]] = {}
# admin_ids = {
#     -10012345678: {12345678}
# }

user_ids: Dict[int, Dict[str, Union[float, Dict[int, int], Set[int]]]] = {}
# user_ids = {
#     12345678: {
#         "ban": {-10012345678},
#         "locked": {-10012345678},
#         "score": 1,
#         "warn": {
#             -10012345678: 0
#         },
#         "waiting": {-10012345678}
#     }
# }

# Init data variables

configs: Dict[int, Dict[str, Union[bool, int, Dict[str, bool]]]] = {}
# configs = {
#     -10012345678: {
#         "default": True,
#         "limit": 3,
#         "locked": 0,
#         "mention": False,
#         "report": {
#             "auto": False,
#             "manual": False
#         }
#     }
# }

# Load data
file_list: List[str] = ["admin_ids", "configs", "user_ids"]
for file in file_list:
    try:
        try:
            if exists(f"data/{file}") or exists(f"data/.{file}"):
                with open(f"data/{file}", 'rb') as f:
                    locals()[f"{file}"] = pickle.load(f)
            else:
                with open(f"data/{file}", 'wb') as f:
                    pickle.dump(eval(f"{file}"), f)
        except Exception as e:
            logger.error(f"Load data {file} error: {e}")
            with open(f"data/.{file}", 'rb') as f:
                locals()[f"{file}"] = pickle.load(f)
    except Exception as e:
        logger.critical(f"Load data {file} backup error: {e}")
        raise SystemExit("[DATA CORRUPTION]")

# Read data from config.ini

# [basic]
bot_token: str = ""
prefix: List[str] = []
prefix_str: str = "/!"

# [bots]
captcha_id: int = 0
clean_id: int = 0
lang_id: int = 0
noflood_id: int = 0
noporn_id: int = 0
nospam_id: int = 0
user_id: int = 0
warn_id: int = 0

# [channels]
debug_channel_id: int = 0
exchange_channel_id: int = 0
logging_channel_id: int = 0
test_group_id: int = 0
logging_channel_username: str = ""

# [custom]
default_group_link: str = ""
project_link: str = ""
project_name: str = ""
reset_day: str = ""
user_name: str = ""

# [encrypt]
password: str = ""

try:
    config = RawConfigParser()
    config.read("config.ini")
    # [basic]
    bot_token = config["basic"].get("bot_token", bot_token)
    prefix = list(config["basic"].get("prefix", prefix_str))
    # [bots]
    captcha_id = int(config["bots"].get("captcha_id", captcha_id))
    clean_id = int(config["bots"].get("clean_id", clean_id))
    lang_id = int(config["bots"].get("lang_id", lang_id))
    noflood_id = int(config["bots"].get("noflood_id", noflood_id))
    noporn_id = int(config["bots"].get("noporn_id", noporn_id))
    nospam_id = int(config["bots"].get("nospam_id", nospam_id))
    user_id = int(config["bots"].get("user_id", user_id))
    warn_id = int(config["bots"].get("warn_id", warn_id))
    # [channels]
    debug_channel_id = int(config["channels"].get("debug_channel_id", debug_channel_id))
    exchange_channel_id = int(config["channels"].get("exchange_channel_id", exchange_channel_id))
    logging_channel_id = int(config["channels"].get("logging_channel_id", logging_channel_id))
    test_group_id = int(config["channels"].get("test_group_id", test_group_id))
    logging_channel_username = config["channels"].get("logging_channel_username", logging_channel_username)
    # [custom]
    default_group_link = config["custom"].get("default_group_link", default_group_link)
    project_link = config["custom"].get("project_link", project_link)
    project_name = config["custom"].get("project_name", project_name)
    reset_day = config["custom"].get("reset_day", reset_day)
    user_name = config["custom"].get("user_name", user_name)
    # [encrypt]
    password = config["encrypt"].get("password", password)
except Exception as e:
    logger.warning(f"Read data from config.ini error: {e}", exc_info=True)

# Check
if (bot_token in {"", "[DATA EXPUNGED]"}
        or prefix == []
        or user_id == 0
        or debug_channel_id == 0
        or exchange_channel_id == 0
        or logging_channel_id == 0
        or test_group_id == 0
        or logging_channel_username in {"", "[DATA EXPUNGED]"}
        or default_group_link in {"", "[DATA EXPUNGED]"}
        or project_link in {"", "[DATA EXPUNGED]"}
        or project_name in {"", "[DATA EXPUNGED]"}
        or reset_day in {"", "[DATA EXPUNGED]"}
        or user_name in {"", "[DATA EXPUNGED]"}
        or password in {"", "[DATA EXPUNGED]"}):
    logger.critical("No proper settings")
    raise SystemExit('No proper settings')

bot_ids: Set[int] = {user_id}

# Start program
copyright_text = (f"SCP-079-WARN v{version}, Copyright (C) 2019 SCP-079 <https://scp-079.org>\n"
                  "Licensed under the terms of the GNU General Public License v3 or later (GPLv3+)\n")
print(copyright_text)
