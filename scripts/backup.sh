#!/bin/bash
# Linux/Mac Backup Script - Add to crontab
# 0 2 * * * /path/to/MoneyPrint/scripts/backup.sh

cd "$(dirname "$0")/.."
source backend/venv/bin/activate
python scripts/backup.py --compress --rotate 30
