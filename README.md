# Orlando Police Department Active Calls Slack Alert Bot

A Python bot that monitors the Orlando Police Department's active calls XML feed and posts alerts to a Slack channel when new incidents match your watch zone/corridor.

## Features

- **Real-time Monitoring**: Polls the OPD active calls feed every 60 seconds (configurable)
- **Smart Filtering**: Detects incidents in your watch corridor using keyword matching on location text
- **Deduplication**: Tracks seen incidents in a local JSON file to avoid duplicate alerts
- **Slack Integration**: Posts formatted alerts with incident details and Google Maps link
- **Robust Error Handling**: Gracefully handles network errors and continues polling
- **Windows-Friendly**: Simple batch file launcher and setup process
- **No Geocoding Required**: Works without external APIs (optional geocoding support for future expansion)

## Prerequisites

- Windows 10/11
- Python 3.7 or higher
- A Slack Incoming Webhook URL (free Slack workspace)

## Setup Instructions

### 1. Create Project Folder

```bash
mkdir OpdBot
cd OpdBot
```

### 2. Create Python Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install requests xmltodict python-dateutil
```

These packages provide:
- **requests**: HTTP library for fetching the XML feed
- **xmltodict**: XML parsing (handles nested structures)
- **python-dateutil**: Date/time handling (optional, included for future enhancements)

### 5. Configure Slack Webhook

You need a Slack Incoming Webhook URL to post alerts:

#### Getting a Slack Webhook URL:

1. Go to your Slack workspace settings: https://api.slack.com/apps
2. Click "Create New App" > "From scratch"
3. Give it a name (e.g., "OPD Alert Bot")
4. Select your workspace and click "Create App"
5. Go to "Incoming Webhooks" in the left menu
6. Toggle "Activate Incoming Webhooks" to ON
7. Click "Add New Webhook to Workspace"
8. Select the channel where alerts should post (e.g., #opd-alerts)
9. Click "Allow"
10. Copy the Webhook URL (starts with https://hooks.slack.com/...)

#### Set Environment Variable (Windows):

**Option A: Permanent (recommended)**
- Right-click "This PC" or "My Computer" → Properties
- Click "Advanced system settings"
- Click "Environment Variables..."
- Click "New..." under "User variables"
- Variable name: `SLACK_WEBHOOK_URL`
- Variable value: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
- Click OK and restart

**Option B: Temporary (session only)**
```bash
set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 6. Run the Bot

**Option A: Using the batch launcher (recommended)**
```bash
run_bot.bat
```

**Option B: Manual (with venv activated)**
```bash
python opd_slack_bot.py
```

## Configuration

All configuration is via environment variables or the script itself:

```python
# Polling interval (seconds)
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))

# Slack webhook (required for alerts)
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Watch zone corridor keywords
CORRIDOR_KEYWORDS = [
    "MILLS",      # Mills Ave
    "ORANGE",     # Orange Ave / Orange Blvd
    "ORLANDO AVE", # Orlando Avenue
    "17/92",      # US-17/92
    "US 17",      # US-17
    "LEE RD",     # Lee Road
    "VIRGINIA DR", # Virginia Drive
    "HORATIO",    # Horatio Street
]
```

### Setting Custom Poll Interval

```bash
set POLL_INTERVAL=30
python opd_slack_bot.py
```

## Deduplication

The bot maintains a `seen_incidents.json` file in the script directory that stores incident numbers it has already alerted on. This prevents duplicate alerts:

```json
{
  "incidents": [
    "202501011234567",
    "202501011234568",
    "202501011234569"
  ]
}
```

If you want to reset and re-alert on old incidents, simply delete this file.

## Feed Structure Reference

The OPD feed provides incident data with these fields:

- **IncidentNumber**: Unique identifier for the incident
- **DateTime**: When the call came in
- **CallType**: Type of incident (Accident, Alarm, Assault, etc.)
- **IncidentLocation**: Street address or intersection
- **District**: Police district (ex: District 1, District 2, etc.)
- **Status**: Active, Closed, etc.

## Example Slack Message

When a new matching incident is detected, the bot posts:

```
🚨 New OPD Active Call

Incident: 202501011234567
Type: Traffic Accident
Time: 2025-01-01 14:30:45
Location: ORANGE AVE & MILLS AVE
District: District 2

[View on Maps] ← clickable button
```

## Logs

The bot logs to console with timestamps:

```
2025-01-01 14:30:45,123 [INFO] Orlando Police Department Active Calls Slack Alert Bot
2025-01-01 14:30:45,124 [INFO] Feed URL: https://www1.cityoforlando.net/opd/activecalls/activecadpolice.xml
2025-01-01 14:30:47,456 [INFO] Found 47 incidents in feed
2025-01-01 14:30:48,789 [INFO] New matching incident found: 202501011234567
2025-01-01 14:30:49,012 [INFO] Posted to Slack: 202501011234567
```

## Troubleshooting

### "Virtual environment not found" error
Make sure you've created the venv:
```bash
python -m venv venv
```

### "ModuleNotFoundError: No module named 'requests'"
Activate the venv and install dependencies:
```bash
venv\Scripts\activate
pip install requests xmltodict python-dateutil
```

### Not receiving Slack alerts
1. Check SLACK_WEBHOOK_URL is set: `echo %SLACK_WEBHOOK_URL%`
2. View console output - it will show if incidents match your corridor keywords
3. Check that the Slack webhook URL is still active (test at https://api.slack.com/apps)
4. Look for error messages in the console output

### Getting "Feed parsing error"
The bot tries two XML parsing methods (xmltodict and ElementTree). If both fail:
1. Check your internet connection
2. Verify the feed URL is accessible: https://www1.cityoforlando.net/opd/activecalls/activecadpolice.xml
3. The feed might be temporarily down (unrelated to the bot)

### To modify watch corridor keywords
Edit `opd_slack_bot.py` and change the `CORRIDOR_KEYWORDS` list:

```python
CORRIDOR_KEYWORDS = [
    "MILLS",
    "ORANGE",
    "YOUR_KEYWORD_HERE",
]
```

## Running as a Background Service

To run the bot continuously on Windows startup:

1. Open Task Scheduler (search "Task Scheduler" in Start menu)
2. Click "Create Basic Task..."
3. Name: "OPD Alert Bot"
4. Trigger: "At startup"
5. Action: Start a program
   - Program/script: `C:\full\path\to\OpdBot\run_bot.bat`
   - Start in: `C:\full\path\to\OpdBot`
6. Check "Run with highest privileges"
7. Click Finish

## Files Structure

```
OpdBot/
├── opd_slack_bot.py          # Main bot script
├── run_bot.bat               # Windows launcher
├── seen_incidents.json       # Generated on first run (dedup file)
└── README.md                 # This file
```

## Performance Notes

- The bot keeps minimal memory footprint (<50 MB)
- Network timeout is 10 seconds per request
- Feed polling is efficient (small XML ~10-50 KB)
- JSON dedup file grows ~1 KB per 50 incidents over months

## License

Created for personal use with Orlando Police public data.

## Support

For issues with the bot:
1. Check console output for error messages
2. Verify internet connection
3. Confirm Slack webhook is active
4. Check that incident locations contain your corridor keywords

---

**Last Updated**: January 2025
**Compatible With**: Windows 10/11, Python 3.7+
