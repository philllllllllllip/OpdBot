@echo off
REM Orlando Police Active Calls Slack Alert Bot - Windows Launcher
REM This script activates the Python virtual environment and runs the bot.

setlocal enabledelayedexpansion

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo ERROR: Virtual environment not found!
    echo Please run setup first:
    echo   python -m venv venv
    echo   venv\Scripts\pip install requests xmltodict python-dateutil
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if SLACK_WEBHOOK_URL is set
if "!SLACK_WEBHOOK_URL!"=="" (
    echo.
    echo WARNING: SLACK_WEBHOOK_URL environment variable is not set.
    echo The bot will run but will only log to console (no Slack alerts).
    echo.
    echo To enable Slack alerts, set the environment variable:
    echo   set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
    echo.
    pause
)

REM Run the bot
echo.
echo Starting Orlando Police Active Calls Slack Alert Bot...
echo Press Ctrl+C to stop.
echo.

python opd_slack_bot.py

REM If the bot exits, show a message and pause
echo.
echo Bot has exited. Press any key to close this window...
pause
