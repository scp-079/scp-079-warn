# SCP-079-WARN

This bot is used to warn or ban someone in group by admin commands.

## How to use

See [this article](https://scp-079.org/warn/).

## To Do List

- [x] Warn or ban someone
- [x] Forgive feature
- [x] Support response the reply to report message
- [x] Interfacing with the whole project database
- [x] Managed by SCP-079-CONFIG
- [x] Support the HIDE channel
- [x] Show more details
- [x] Follow the hard core interaction principle

## Requirements

- Python 3.6 or higher.
- `requirements.txt` ： APScheduler pyAesCrypt pyrogram[fast]

## Files

- plugins
    - functions
        - `channel.py` : Send messages to channel
        - `etc.py` : Miscellaneous
        - `file.py` : Save files
        - `filters.py` : Some filters
        - `group.py` : Functions about group
        - `ids.py` : Modify id lists
        - `telegram.py` : Some telegram functions
        - `timers.py` : Timer functions
        - `user.py` : Functions about user
    - handlers
        - `callback.py` : Handle callbacks
        - `command` : Handle commands
        - `message.py`: Handle messages
    - `glovar.py` : Global variables
- `.gitignore` : Ignore
- `config.ini.example` -> `config.ini` : Configures
- `LICENSE` : GPLv3
- `main.py` : Start here
- `README.md` : This file
- `requirements.txt` : Managed by pip

## Contribute

Welcome to make this project even better. You can submit merge requests, or report issues.

## License

Licensed under the terms of the [GNU General Public License v3](LICENSE).
