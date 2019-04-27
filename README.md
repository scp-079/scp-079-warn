# SCP-079-WARN

This bot is used to warn or ban someone in group by admin commands.

## How to use

See [this article](https://scp-079.org/warn/).

## Features

- Easy to use
- Can merge similar or mutually contained rules
- Search patterns
- Test patterns

## To Do List

- [x] Complete phrase management for a single group
- [x] Check the pattern before add
- [x] Choose the right way to store data
- [x] Interfacing with the whole project database
- [x] Search for patterns in more ways
- [x] Test patterns in a group
- [x] Simplified Chinese to Traditional Chinese
- [x] Copy the same pattern to other groups

## Requirements

- Python 3.6 or higher.
- `requirements.txt` ： APScheduler pyAesCrypt pyrogram[fast]

## Files

- plugins
    - functions
        - `etc.py` : Miscellaneous
        - `files.py` : Save files
        - `filters.py` : Some filters
        - `telegram.py` : Some telegram functions
        - `timer.py` : Timer functions
        - `words.py` : Manage words
    - handlers
        - `callbacks.py` : Handle callbacks
        - `commands` : Handle commands
        - `messages.py`: Handle messages
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
