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
from threading import Lock
from typing import Dict, List, Set, Tuple, Union

from pyrogram import Chat

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    filename="log",
    filemode="w"
)
logger = logging.getLogger(__name__)

# Read data from config.ini

# [basic]
bot_token: str = ""
prefix: List[str] = []
prefix_str: str = "/!"

# [bots]
avatar_id: int = 0
captcha_id: int = 0
clean_id: int = 0
lang_id: int = 0
long_id: int = 0
noflood_id: int = 0
noporn_id: int = 0
nospam_id: int = 0
recheck_id: int = 0
tip_id: int = 0
user_id: int = 0
warn_id: int = 0

# [channels]
critical_channel_id: int = 0
debug_channel_id: int = 0
exchange_channel_id: int = 0
hide_channel_id: int = 0
logging_channel_id: int = 0
test_group_id: int = 0

# [custom]
aio: Union[bool, str] = ""
backup: Union[bool, str] = ""
date_reset: str = ""
default_group_link: str = ""
limit_ban: int = 0
project_link: str = ""
project_name: str = ""
zh_cn: Union[bool, str] = ""

# [encrypt]
key: Union[bytes, str] = ""
password: str = ""

try:
    config = RawConfigParser()
    config.read("config.ini")
    # [basic]
    bot_token = config["basic"].get("bot_token", bot_token)
    prefix = list(config["basic"].get("prefix", prefix_str))
    # [bots]
    avatar_id = int(config["bots"].get("avatar_id", avatar_id))
    captcha_id = int(config["bots"].get("captcha_id", captcha_id))
    clean_id = int(config["bots"].get("clean_id", clean_id))
    lang_id = int(config["bots"].get("lang_id", lang_id))
    long_id = int(config["bots"].get("long_id", long_id))
    noflood_id = int(config["bots"].get("noflood_id", noflood_id))
    noporn_id = int(config["bots"].get("noporn_id", noporn_id))
    nospam_id = int(config["bots"].get("nospam_id", nospam_id))
    recheck_id = int(config["bots"].get("recheck_id", recheck_id))
    tip_id = int(config["bots"].get("tip_id", tip_id))
    user_id = int(config["bots"].get("user_id", user_id))
    warn_id = int(config["bots"].get("warn_id", warn_id))
    # [channels]
    critical_channel_id = int(config["channels"].get("critical_channel_id", critical_channel_id))
    debug_channel_id = int(config["channels"].get("debug_channel_id", debug_channel_id))
    exchange_channel_id = int(config["channels"].get("exchange_channel_id", exchange_channel_id))
    hide_channel_id = int(config["channels"].get("hide_channel_id", hide_channel_id))
    logging_channel_id = int(config["channels"].get("logging_channel_id", logging_channel_id))
    test_group_id = int(config["channels"].get("test_group_id", test_group_id))
    # [custom]
    aio = config["custom"].get("aio", aio)
    aio = eval(aio)
    backup = config["custom"].get("backup", backup)
    backup = eval(backup)
    date_reset = config["custom"].get("date_reset", date_reset)
    default_group_link = config["custom"].get("default_group_link", default_group_link)
    limit_ban = int(config["custom"].get("limit_ban", limit_ban))
    project_link = config["custom"].get("project_link", project_link)
    project_name = config["custom"].get("project_name", project_name)
    zh_cn = config["custom"].get("zh_cn", zh_cn)
    zh_cn = eval(zh_cn)
    # [encrypt]
    key = config["encrypt"].get("key", key)
    key = key.encode("utf-8")
    password = config["encrypt"].get("password", password)
except Exception as e:
    logger.warning(f"Read data from config.ini error: {e}", exc_info=True)

# Check
if (bot_token in {"", "[DATA EXPUNGED]"}
        or prefix == []
        or avatar_id == 0
        or captcha_id == 0
        or clean_id == 0
        or lang_id == 0
        or long_id == 0
        or noflood_id == 0
        or noporn_id == 0
        or nospam_id == 0
        or recheck_id == 0
        or tip_id == 0
        or user_id == 0
        or warn_id == 0
        or critical_channel_id == 0
        or debug_channel_id == 0
        or exchange_channel_id == 0
        or hide_channel_id == 0
        or logging_channel_id == 0
        or test_group_id == 0
        or aio not in {False, True}
        or backup not in {False, True}
        or date_reset in {"", "[DATA EXPUNGED]"}
        or default_group_link in {"", "[DATA EXPUNGED]"}
        or limit_ban == 0
        or project_link in {"", "[DATA EXPUNGED]"}
        or project_name in {"", "[DATA EXPUNGED]"}
        or zh_cn not in {False, True}
        or key in {b"", b"[DATA EXPUNGED]", "", "[DATA EXPUNGED]"}
        or password in {"", "[DATA EXPUNGED]"}):
    logger.critical("No proper settings")
    raise SystemExit("No proper settings")

# Languages
lang: Dict[str, str] = {
    # Admin
    "admin": (zh_cn and "管理员") or "Admin",
    "admin_group": (zh_cn and "群管理") or "Group Admin",
    "admin_project": (zh_cn and "项目管理员") or "Project Admin",
    # Basic
    "action": (zh_cn and "执行操作") or "Action",
    "clear": (zh_cn and "清空数据") or "Clear Data",
    "colon": (zh_cn and "：") or ": ",
    "description": (zh_cn and "说明") or "Description",
    "disabled": (zh_cn and "禁用") or "Disabled",
    "enabled": (zh_cn and "启用") or "Enabled",
    "name": (zh_cn and "名称") or "Name",
    "reason": (zh_cn and "原因") or "Reason",
    "reset": (zh_cn and "重置数据") or "Reset Data",
    "rollback": (zh_cn and "数据回滚") or "Rollback",
    "score": (zh_cn and "评分") or "Score",
    "status_failed": (zh_cn and "未执行") or "Failed",
    "status_succeeded": (zh_cn and "成功执行") or "Succeeded",
    "version": (zh_cn and "版本") or "Version",
    # Command
    "command_lack": (zh_cn and "命令参数缺失") or "Lack of Parameter",
    "command_para": (zh_cn and "命令参数有误") or "Incorrect Command Parameter",
    "command_type": (zh_cn and "命令类别有误") or "Incorrect Command Type",
    "command_usage": (zh_cn and "用法有误") or "Incorrect Usage",
    # Config
    "config": (zh_cn and "设置") or "Settings",
    "config_button": (zh_cn and "请点击下方按钮进行设置") or "Press the Button to Config",
    "config_change": (zh_cn and "更改设置") or "Change Config",
    "config_create": (zh_cn and "创建设置会话") or "Create Config Session",
    "config_go": (zh_cn and "前往设置") or "Go to Config",
    "config_locked": (zh_cn and "设置当前被锁定") or "Config is Locked",
    "config_show": (zh_cn and "查看设置") or "Show Config",
    "config_updated": (zh_cn and "已更新") or "Updated",
    "custom": (zh_cn and "自定义") or "Custom",
    "default": (zh_cn and "默认") or "Default",
    "delete": (zh_cn and "协助删除") or "Help Delete",
    "limit": (zh_cn and "警告上限") or "Warn Limit",
    "mention": (zh_cn and "呼叫管理") or "Mention Admins",
    "report_auto": (zh_cn and "自动举报") or "Auto Report",
    "report_manual": (zh_cn and "手动举报") or "Manual Report",
    # Debug
    "triggered_by": (zh_cn and "触发消息") or "Triggered By",
    # Emergency
    "issue": (zh_cn and "发现状况") or "Issue",
    "exchange_invalid": (zh_cn and "数据交换频道失效") or "Exchange Channel Invalid",
    "auto_fix": (zh_cn and "自动处理") or "Auto Fix",
    "protocol_1": (zh_cn and "启动 1 号协议") or "Initiate Protocol 1",
    "transfer_channel": (zh_cn and "频道转移") or "Transfer Channel",
    "emergency_channel": (zh_cn and "应急频道") or "Emergency Channel",
    # Group
    "group_id": (zh_cn and "群组 ID") or "Group ID",
    "group_name": (zh_cn and "群组名称") or "Group Name",
    "inviter": (zh_cn and "邀请人") or "Inviter",
    "leave_auto": (zh_cn and "自动退出并清空数据") or "Leave automatically",
    "leave_approve": (zh_cn and "已批准退出群组") or "Approve to Leave the Group",
    "reason_admin": (zh_cn and "获取管理员列表失败") or "Failed to Fetch Admin List",
    "reason_leave": (zh_cn and "非管理员或已不在群组中") or "Not Admin in Group",
    "reason_none": (zh_cn and "无数据") or "No Data",
    "reason_permissions": (zh_cn and "权限缺失") or "Missing Permissions",
    "reason_unauthorized": (zh_cn and "未授权使用") or "Unauthorized",
    "reason_user": (zh_cn and "缺失 USER") or "Missing USER",
    "refresh": (zh_cn and "刷新群管列表") or "Refresh Admin Lists",
    "status_joined": (zh_cn and "已加入群组") or "Joined the Group",
    "status_left": (zh_cn and "已退出群组") or "Left the Group",
    # More
    "privacy": (zh_cn and "可能涉及隐私而未转发") or "Not Forwarded Due to Privacy Reason",
    "cannot_forward": (zh_cn and "此类消息无法转发至频道") or "The Message Cannot be Forwarded to Channel",
    # Message Types
    "gam": (zh_cn and "游戏") or "Game",
    "ser": (zh_cn and "服务消息") or "Service",
    # Record
    "project": (zh_cn and "项目编号") or "Project",
    "project_origin": (zh_cn and "原始项目") or "Original Project",
    "status": (zh_cn and "状态") or "Status",
    "user_id": (zh_cn and "用户 ID") or "User ID",
    "level": (zh_cn and "操作等级") or "Level",
    "rule": (zh_cn and "规则") or "Rule",
    "message_type": (zh_cn and "消息类别") or "Message Type",
    "message_game": (zh_cn and "游戏标识") or "Game Short Name",
    "message_lang": (zh_cn and "消息语言") or "Message Language",
    "message_len": (zh_cn and "消息长度") or "Message Length",
    "message_freq": (zh_cn and "消息频率") or "Message Frequency",
    "user_score": (zh_cn and "用户得分") or "User Score",
    "user_bio": (zh_cn and "用户简介") or "User Bio",
    "user_name": (zh_cn and "用户昵称") or "User Name",
    "from_name": (zh_cn and "来源名称") or "Forward Name",
    "contact": (zh_cn and "联系方式") or "Contact Info",
    "more": (zh_cn and "附加信息") or "Extra Info",
    # Special
    "abuse": (zh_cn and "滥用") or "Abuse",
    "abuse_mention": (zh_cn and "群管认定滥用呼叫功能") or "Abuse Mention Function",
    "abuse_report": (zh_cn and "群管认定滥用举报功能") or "Abuse Report Function",
    "action_answer": (zh_cn and "处理举报") or "Answer Report",
    "action_ban": (zh_cn and "封禁用户") or "Ban User",
    "action_cancel": (zh_cn and "取消举报") or "Cancel Report",
    "action_forgive": (zh_cn and "重置用户状态") or "Forgive User",
    "action_kick": (zh_cn and "移除用户") or "Kick User",
    "action_unban": (zh_cn and "解禁用户") or "Undo Ban",
    "action_undo": (zh_cn and "撤销操作") or "Undo Operation",
    "action_unwait": (zh_cn and "重置举报状态") or "Reset Report Status",
    "action_unwarn": (zh_cn and "撤销警告") or "Undo Warn",
    "action_unwarns": (zh_cn and "清空警告") or "Clear Warns",
    "action_warn": (zh_cn and "警告用户") or "Warn User",
    "answer_proceeded": (zh_cn and "已被其他管理员处理") or "",
    "auto_triggered": (zh_cn and "自动触发") or "Auto Triggered",
    "ban": (zh_cn and "封禁") or "Ban",
    "ban_reason": (zh_cn and "封禁原因") or "Ban Reason",
    "by_button": (zh_cn and "举报或呼叫") or "Report or Mention",
    "cancel": (zh_cn and "取消") or "Cancel",
    "del": (zh_cn and "删除") or "Delete",
    "description_by_admin": (zh_cn and "此操作由本群管理员执行") or "This Operation is Performed by the Group Admin",
    "description_wait_admin": (zh_cn and "此举报需本群管理员处置") or "This Report Needs to be Viewed by the Group Admin",
    "expired": (zh_cn and "会话已失效") or "Session Expired",
    "from_self": (zh_cn and "群管直接回复汇报消息") or "The Group Admin Directly Replied to the Report Message",
    "from_user": (zh_cn and "来自用户") or "From User",
    "mention_admins": (zh_cn and "呼叫管理") or "Mention Admins",
    "reason_abuse": (zh_cn and "滥用机器人功能") or "Abuse",
    "reason_deleted": (zh_cn and "消息已被删除") or "Message Has Been Deleted",
    "reason_banned": (zh_cn and "已在封禁列表中") or "Already in the Banned List",
    "reason_limit": (zh_cn and "警告次数达到上限") or "Reach the Limit of Warnings",
    "reported_message": (zh_cn and "被举报消息") or "Reported Message",
    "reported_name": (zh_cn and "被举报昵称") or "Reported Name",
    "reported_user": (zh_cn and "被举报用户") or "Reported User",
    "reporter": (zh_cn and "举报人") or "Reporter",
    "rule_admin": (zh_cn and "群管自行操作") or "Group Admin's Command",
    "stored_message": (zh_cn and "消息存放") or "Stored Message",
    "warn": (zh_cn and "警告") or "Warn",
    "warn_undo": (zh_cn and "撤销警告") or "Undo Warn",
    "unban": (zh_cn and "解禁") or "Unban",
    "undo": (zh_cn and "撤销") or "Undo",
    "user_banned": (zh_cn and "已封禁用户") or "Banned User",
    "user_kicked": (zh_cn and "已移除用户") or "Kicked User",
    "user_unbanned": (zh_cn and "已解禁用户") or "Unbanned User",
    "user_unwarned": (zh_cn and "已撤销警告") or "Unwarned User",
    "user_warned": (zh_cn and "已警告用户") or "Warned User",
    "user_warns": (zh_cn and "该用户警告统计") or "User Warns",
    # Terminate
    "auto_ban": (zh_cn and "自动封禁") or "Auto Ban",
    "auto_delete": (zh_cn and "自动删除") or "Auto Delete",
    "global_delete": (zh_cn and "全局删除") or "Global Delete",
    "name_ban": (zh_cn and "名称封禁") or "Ban by Name",
    "name_examine": (zh_cn and "名称检查") or "Name Examination",
    "name_recheck": (zh_cn and "名称复查") or "Name Recheck",
    "op_downgrade": (zh_cn and "操作降级") or "Operation Downgrade",
    "op_upgrade": (zh_cn and "操作升级") or "Operation Upgrade",
    "rule_custom": (zh_cn and "群组自定义") or "Custom Rule",
    "rule_global": (zh_cn and "全局规则") or "Global Rule",
    "score_ban": (zh_cn and "评分封禁") or "Ban by Score",
    "score_user": (zh_cn and "用户评分") or "High Score",
    "watch_ban": (zh_cn and "追踪封禁") or "Watch Ban",
    "watch_delete": (zh_cn and "追踪删除") or "Watch Delete",
    "watch_user": (zh_cn and "敏感追踪") or "Watched User"
}

# Init

all_commands: List[str] = [
    "admin",
    "admins",
    "ban",
    "config",
    "config_warn",
    "forgive",
    "kick",
    "report",
    "unban",
    "undo",
    "version",
    "warn"
]

bot_ids: Set[int] = {avatar_id, captcha_id, clean_id, lang_id, long_id, noflood_id,
                     noporn_id, nospam_id, recheck_id, tip_id, user_id, warn_id}

chats: Dict[int, Chat] = {}
# chats = {
#     -10012345678: Chat
# }

counts: Dict[int, Dict[int, int]] = {}
# counts = {
#     -10012345678: {
#         12345678: 1
#     }
# }

declared_message_ids: Dict[int, Set[int]] = {}
# declared_message_ids = {
#     -10012345678: {123}
# }

default_config: Dict[str, Union[bool, int, Dict[str, bool]]] = {
    "default": True,
    "lock": 0,
    "delete": True,
    "limit": 3,
    "mention": True,
    "report": {
        "auto": False,
        "manual": True
    }
}

default_user_status: Dict[str, Union[float, Dict[Union[int, str], Union[float, int]], Set[int]]] = {
    "ban": set(),
    "kick": set(),
    "lock": set(),
    "score": {
        "captcha": 0.0,
        "clean": 0.0,
        "lang": 0.0,
        "long": 0.0,
        "noflood": 0.0,
        "noporn": 0.0,
        "nospam": 0.0,
        "recheck": 0.0,
        "warn": 0.0
    },
    "warn": {},
    "waiting": set()
}

locks: Dict[str, Lock] = {
    "admin": Lock(),
    "message": Lock(),
    "receive": Lock()
}

receivers: Dict[str, List[str]] = {
    "score": ["ANALYZE", "CAPTCHA", "CLEAN", "LANG", "LONG", "MANAGE",
              "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "TIP", "USER", "WARN", "WATCH"],
}

sender: str = "WARN"

should_hide: bool = False

usernames: Dict[str, Dict[str, Union[int, str]]] = {}
# usernames = {
#     "SCP_079": {
#         "peer_type": "channel",
#         "peer_id": -1001196128009
#     }
# }

version: str = "0.3.9"

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

bad_ids: Dict[str, Set[int]] = {
    "users": set()
}
# bad_ids = {
#     "users": {12345678}
# }

left_group_ids: Set[int] = set()
# left_group_ids = {-10012345678}

message_ids: Dict[int, Tuple[int, int]] = {}
# message_ids = {
#     -10012345678: (123, 1512345678)
# }

user_ids: Dict[int, Dict[str, Union[float, Dict[Union[int, str], Union[float, int]], Set[int]]]] = {}
# user_ids = {
#     12345678: {
#         "ban": {-10012345675},
#         "kick": {-10012345676},
#         "lock": {-10012345677},
#         "score": {
#             "captcha": 0.0,
#             "clean": 0.0,
#             "lang": 0.0,
#             "long": 0.0,
#             "noflood": 0.0,
#             "noporn": 0.0,
#             "nospam": 0.0,
#             "recheck": 0.0,
#             "warn": 1.7
#         }
#         "warn": {
#             -10012345678: 0
#         },
#         "waiting": {-10012345679}
#     }
# }

watch_ids: Dict[str, Dict[int, int]] = {
    "ban": {},
    "delete": {}
}
# watch_ids = {
#     "ban": {
#         12345678: 1512345678
#     },
#     "delete": {
#         12345678: 1512345678
#     }
# }

# Init data variables

configs: Dict[int, Dict[str, Union[bool, int, Dict[str, bool]]]] = {}
# configs = {
#     -10012345678: {
#         "default": True,
#         "limit": 3,
#         "lock": 0,
#         "mention": False,
#         "report": {
#             "auto": False,
#             "manual": False
#         }
#     }
# }

reports: Dict[str, Dict[str, Union[int, str]]] = {}
# reports = {
#     "random": {
#         "time": 1512345678
#         "group_id": -10012345678,
#         "reporter_id": 12345678,
#         "user_id": 12345679,
#         "message_id": 123,
#         "report_id": 124,
#         "reason": None
#     }
# }

# Load data
file_list: List[str] = ["admin_ids", "bad_ids", "left_group_ids", "message_ids", "user_ids", "watch_ids",
                        "configs", "reports"]
for file in file_list:
    try:
        try:
            if exists(f"data/{file}") or exists(f"data/.{file}"):
                with open(f"data/{file}", "rb") as f:
                    locals()[f"{file}"] = pickle.load(f)
            else:
                with open(f"data/{file}", "wb") as f:
                    pickle.dump(eval(f"{file}"), f)
        except Exception as e:
            logger.error(f"Load data {file} error: {e}", exc_info=True)
            with open(f"data/.{file}", "rb") as f:
                locals()[f"{file}"] = pickle.load(f)
    except Exception as e:
        logger.critical(f"Load data {file} backup error: {e}", exc_info=True)
        raise SystemExit("[DATA CORRUPTION]")

# Start program
copyright_text = (f"SCP-079-{sender} v{version}, Copyright (C) 2019 SCP-079 <https://scp-079.org>\n"
                  "Licensed under the terms of the GNU General Public License v3 or later (GPLv3+)\n")
print(copyright_text)
