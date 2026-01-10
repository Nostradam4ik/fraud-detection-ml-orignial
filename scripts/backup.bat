@echo off
REM Windows Backup Script - Run daily via Task Scheduler
REM Schedule: schtasks /create /tn "FraudDetectionBackup" /tr "D:\Code\MoneyPrint\scripts\backup.bat" /sc daily /st 02:00

cd /d D:\Code\MoneyPrint
call backend\venv\Scripts\activate
python scripts\backup.py --compress --rotate 30
