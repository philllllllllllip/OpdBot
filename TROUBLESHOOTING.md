# OPD Slack Alert Bot - Troubleshooting Guide

This guide covers common issues and how to fix them.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Slack Integration Issues](#slack-integration-issues)
3. [Feed and Filtering Issues](#feed-and-filtering-issues)
4. [Bot Behavior Issues](#bot-behavior-issues)
5. [Performance Issues](#performance-issues)
6. [Advanced Debugging](#advanced-debugging)

---

## Installation Issues

### Issue: "Python is not recognized as an internal or external command"

**Symptoms**:
- When running `python` or `python --version`, you get "not recognized" error
- `setup.bat` fails immediately

**Cause**: Python is not installed or not in your system PATH

**Solutions**:

1. **Check if Python is installed**:
   ```bash
   python --version
   ```
   
   If no output, Python is not installed.

2. **Install Python**:
   - Download from https://www.python.org/downloads/
   - During installation, **CHECK "Add Python to PATH"** ← Important!
   - Complete installation
   - Restart Command Prompt
   - Try again: `python --version`

3. **Alternative: Use full path**:
   ```bash
   C:\Python311\python opd_slack_bot.py
   ```
   (Replace `Python311` with your actual Python version)

4. **Verify PATH variable**:
   ```bash
   echo %PATH%
   ```
   Should contain something like `C:\Python311\` or `C:\Users\...\AppData\Local\Programs\Python\`

---

### Issue: "ModuleNotFoundError: No module named 'requests'"

**Symptoms**:
- Bot crashes with this error immediately
- `ImportError: No module named 'xmltodict'`
- `ImportError: No module named 'python_dateutil'`

**Cause**: Dependencies not installed, or wrong Python environment

**Solutions**:

1. **Verify virtual environment is set up**:
   ```bash
   # Check if venv exists
   dir venv
   
   # If not, create it:
   python -m venv venv
   ```

2. **Activate virtual environment and install dependencies**:
   ```bash
   # Activate
   venv\Scripts\activate
   
   # Install
   pip install requests xmltodict python-dateutil
   
   # Or use requirements.txt:
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python -c "import requests; print(requests.__version__)"
   python -c "import xmltodict; print(xmltodict.__version__)"
   ```

4. **If still failing, try upgrading pip**:
   ```bash
   python -m pip install --upgrade pip
   pip install requests xmltodict python-dateutil
   ```

---

### Issue: "Virtual environment not found" (when using run_bot.bat)

**Symptoms**:
- When running `run_bot.bat`, it says venv not found
- Need to set up virtual environment

**Solution**:

```bash
# Open Command Prompt in the OpdBot folder
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Now run the bot
run_bot.bat
```

---

## Slack Integration Issues

### Issue: Bot runs but Slack messages not appearing

**Symptoms**:
- Console shows `[INFO] Posted to Slack: ...`
- But no message in Slack channel
- Or console shows `[ERROR] Failed to post to Slack`

**Diagnostic steps**:

1. **Check webhook URL is set**:
   ```bash
   echo %SLACK_WEBHOOK_URL%
   ```
   Should show the URL. If empty, go to step 4.

2. **Verify webhook URL format**:
   - Should be: `https://hooks.slack.com/services/T00000000/B00000000/XXXXX`
   - Should start with `https://hooks.slack.com/`
   - Should be long (100+ characters)

3. **Test webhook manually**:
   
   **PowerShell**:
   ```powershell
   $json = @{"text"="Test message from OPD Bot"} | ConvertTo-Json
   Invoke-WebRequest -Uri "YOUR_WEBHOOK_URL" -Method Post -Body $json -ContentType "application/json"
   ```
   
   Should return status 200 with body "ok"

4. **Set SLACK_WEBHOOK_URL environment variable**:
   
   **Temporary (test)**:
   ```bash
   set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   python opd_slack_bot.py
   ```
   
   **Permanent**:
   - Right-click "This PC" → Properties
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - New User variable:
     - Name: `SLACK_WEBHOOK_URL`
     - Value: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
   - Restart Command Prompt and verify: `echo %SLACK_WEBHOOK_URL%`

5. **Check Slack app permissions**:
   - Go to https://api.slack.com/apps
   - Select your app
   - Check "Incoming Webhooks" is toggled ON
   - Check webhook is enabled and not deleted
   - Webhook should match the channel you're posting to

6. **Check channel permissions**:
   - Make sure the bot can post to the channel
   - Try a different channel (create #test-opd-alerts)
   - Re-create the webhook for that channel

---

### Issue: "Webhook URL invalid" or "403 Forbidden"

**Symptoms**:
- Console shows `Failed to post to Slack: 403 Client Error`
- Or `Webhook URL invalid`

**Causes**:
- Webhook URL is incorrect or expired
- Webhook was deleted or revoked
- Webhook is for a different app or workspace

**Solutions**:

1. **Verify webhook still exists**:
   - Go to https://api.slack.com/apps
   - Select your app
   - Go to "Incoming Webhooks"
   - If you don't see your webhook, it was deleted

2. **Generate a new webhook**:
   - In Incoming Webhooks, click "Add New Webhook to Workspace"
   - Select the channel
   - Click "Allow"
   - Copy the new webhook URL
   - Update environment variable: `set SLACK_WEBHOOK_URL=...`

3. **Verify you have API credentials**:
   - Check you created the app in the correct workspace
   - Use your workspace's API page, not someone else's

---

### Issue: Webhook configured but warning about "Slack webhook not configured"

**Symptoms**:
- Console shows: `WARNING: Slack webhook not configured; skipping post`
- But you set `SLACK_WEBHOOK_URL`

**Cause**: Environment variable not recognized by the script

**Solution**:

1. **Restart Command Prompt/PowerShell**:
   - Close all command prompts
   - Open a new one
   - Try: `echo %SLACK_WEBHOOK_URL%`

2. **If still not working, set it temporary**:
   ```bash
   set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   python opd_slack_bot.py
   ```

3. **Verify environment variable**:
   ```bash
   set | findstr SLACK_WEBHOOK_URL
   ```
   Should show your webhook URL

---

## Feed and Filtering Issues

### Issue: Bot is running but no alerts appear (and no errors)

**Symptoms**:
- Console shows "Found X incidents in feed"
- But no "[INFO] New matching incident found" messages
- No Slack messages either

**Cause**: Incidents don't match your corridor keywords, OR all are already seen

**Diagnostic steps**:

1. **Enable DEBUG logging**:
   
   Edit `opd_slack_bot.py`:
   ```python
   logging.basicConfig(
       level=logging.DEBUG,  # Change from INFO to DEBUG
       ...
   )
   ```
   
   Save and restart bot.

2. **Look for these debug messages**:
   ```
   [DEBUG] Incident 202501011234567 location 'SEMORAN BLVD' does not match corridor
   [DEBUG] Already seen incident 202501011234568
   ```
   
   This shows which incidents are being filtered out and why.

3. **Check your corridor keywords**:
   
   In `opd_slack_bot.py`, find:
   ```python
   CORRIDOR_KEYWORDS = [
       "MILLS",
       "ORANGE",
       ...
   ]
   ```
   
   Make sure there are keywords in this list.

4. **Test if any incidents match**:
   
   Look at incident location examples in debug output:
   ```
   Incident 202501011234567 location 'MILLS AVE & ORANGE AVE' does not match corridor
   ```
   
   That location CONTAINS "MILLS", so there's a bug in the matching logic.
   Check the code.

5. **All incidents already seen?**:
   
   If debug shows all incidents as "[DEBUG] Already seen", it means:
   - You've already alerted on them
   - Delete `seen_incidents.json`:
     ```bash
     del seen_incidents.json
     ```
   - Restart bot
   - It will re-alert on current matching incidents

---

### Issue: Incidents match but don't alert

**Symptoms**:
- Debug shows "[INFO] New matching incident found: 202501011234567"
- But no Slack message
- No error in console

**Cause**: SLACK_WEBHOOK_URL not set

**Solution**:
- See [Issue: Bot runs but Slack messages not appearing](#issue-bot-runs-but-slack-messages-not-appearing)

---

### Issue: Getting alerts for locations I don't care about

**Symptoms**:
- Bot alerts on incidents but they're not in your watch zone
- Location contains keywords but shouldn't match

**Cause**: Keywords too broad

**Example**:
```
Keyword: "ORANGE"
Matches: "ORANGE BLOSSOM TRL", "ORANGE AVE", "ORANGE ST"
Accidentally matches: "ORANGE CITY" (different city), "THE ORANGE GROVES" (not a street)
```

**Solutions**:

1. **Make keywords more specific**:
   ```python
   CORRIDOR_KEYWORDS = [
       "MILLS AVE",      # More specific than "MILLS"
       "ORANGE AVE",     # More specific than "ORANGE"
       "VIRGINIA DR",
   ]
   ```

2. **Add more corridor keywords**:
   ```python
   CORRIDOR_KEYWORDS = [
       "MILLS",
       "ORANGE",
       "LEE RD",          # Your actual watch zones only
   ]
   ```

3. **Remove keywords that are too broad**:
   ```python
   # Remove just "ORANGE" if it's causing issues
   # Keep "ORANGE AVE" instead
   CORRIDOR_KEYWORDS = [
       "MILLS",
       "ORANGE AVE",      # More specific
       "LEE RD",
   ]
   ```

---

### Issue: "Feed parsing error" or "No incidents found in feed"

**Symptoms**:
- Console shows: `[WARNING] No incidents found in feed`
- Or: `[WARNING] xmltodict parsing failed`
- Or: `[WARNING] ElementTree parsing failed`

**Cause**: Feed URL is down, or feed format changed

**Diagnostic steps**:

1. **Check internet connection**:
   ```bash
   ping www1.cityoforlando.net
   ```
   Should get responses.

2. **Test feed URL directly**:
   - Open browser
   - Go to: https://www1.cityoforlando.net/opd/activecalls/activecadpolice.xml
   - Should see XML content (lots of `<INCIDENT>` entries)
   - If blank or error, OPD server is down

3. **Check feed structure**:
   - If feed loads but bot can't parse it, the XML structure may have changed
   - Contact support or file an issue

4. **Check network firewall**:
   - Some corporate/school networks block the OPD URL
   - Try using a personal hotspot or home network
   - Check with your network admin

---

## Bot Behavior Issues

### Issue: Bot exits immediately

**Symptoms**:
- Run run_bot.bat or python script
- Bot starts then immediately stops/exits
- No error message or error is hard to read

**Solutions**:

1. **Run from Command Prompt directly** (not double-click):
   ```bash
   python opd_slack_bot.py
   ```
   This shows error messages before the window closes.

2. **Look for error messages**:
   - Check for Python errors
   - Check if dependencies are missing (see Installation Issues)
   - Check if SLACK_WEBHOOK_URL is invalid

3. **Add pause to batch file**:
   
   Edit `run_bot.bat`, change last line to keep window open:
   ```bash
   python opd_slack_bot.py
   pause
   ```

---

### Issue: Bot stops polling after X minutes

**Symptoms**:
- Bot runs for a while then stops
- Last message: `Polling feed at ...`
- No error message

**Cause**: Network connection lost, or OPD server disconnected

**Solutions**:

1. **This is normal behavior**:
   - Network failures happen
   - OPD server can be temporarily down
   - Bot retries next cycle

2. **Check network**:
   ```bash
   ping www1.cityoforlando.net
   ```

3. **Look for error messages in previous output**:
   - Scroll up in console
   - Look for `[ERROR]` lines

4. **Increase request timeout** (if connection is slow):
   
   Edit `opd_slack_bot.py`:
   ```python
   REQUEST_TIMEOUT = 10  # Change to 15 or 20
   ```

---

### Issue: Duplicate alerts for same incident

**Symptoms**:
- Get multiple Slack messages for the same incident
- Seems random or happens after restart

**Cause**: `seen_incidents.json` got corrupted or was deleted

**Solution**:

1. **Check the file exists**:
   ```bash
   type seen_incidents.json
   ```

2. **Verify it's valid JSON**:
   - Open it in a text editor
   - Should look like:
     ```json
     {
       "incidents": ["202501011234567", "202501011234568"]
     }
     ```

3. **If corrupted, delete and restart**:
   ```bash
   del seen_incidents.json
   python opd_slack_bot.py
   ```
   - Bot will recreate it fresh
   - You'll get alerted on all current matching incidents once

4. **Prevent future corruption**:
   - Don't edit `seen_incidents.json` while bot is running
   - Shut down bot before editing it

---

## Performance Issues

### Issue: Bot using lots of memory

**Symptoms**:
- Memory usage increases over time
- Eventually reaches 100% or slows down system

**Cause**: Usually a memory leak (rare) or seen_incidents.json growing large

**Solutions**:

1. **Check seen_incidents.json size**:
   ```bash
   dir seen_incidents.json
   ```
   
   If millions of incidents (file > 10 MB), it's grown too large.

2. **Reset old incidents**:
   ```bash
   del seen_incidents.json
   ```
   
   This removes old incident history but you might get duplicate alerts on current incidents.

3. **Memory usage is normally <50 MB**:
   - If much higher, there may be a memory leak
   - Try restarting the bot periodically:
     ```bash
     # Run in Task Scheduler with daily restart
     ```

---

### Issue: Feed polling is slow (taking minutes)

**Symptoms**:
- Bot says "Polling feed" but takes 30+ seconds to complete
- Only happens once every few minutes/hours

**Cause**: Network latency or OPD server is slow

**Solutions**:

1. **This is usually normal**:
   - Network can be slow sometimes
   - OPD server can have temporary delays

2. **Check your network**:
   ```bash
   ping -c 5 www1.cityoforlando.net
   ```
   Look for high response times (>500ms is slow)

3. **Increase timeout if network is slow**:
   
   Edit `opd_slack_bot.py`:
   ```python
   REQUEST_TIMEOUT = 20  # Give more time
   ```

4. **Reduce polling frequency if not needed**:
   
   ```bash
   set POLL_INTERVAL=120  # Poll every 2 minutes instead of 1
   python opd_slack_bot.py
   ```

---

## Advanced Debugging

### Enabling Full Debug Output

Edit `opd_slack_bot.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # <- Change this from INFO
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
```

Debug output shows:
- Every incident being processed
- Why incidents are skipped
- Exact error messages
- Network request details

### Capturing Output to File

**PowerShell**:
```powershell
python opd_slack_bot.py | Tee-Object bot.log
```

**Command Prompt**:
```bash
python opd_slack_bot.py > bot.log 2>&1
```

Then view: `type bot.log`

### Testing XML Parsing Directly

```python
# Run this in Python to test if feed can be parsed:
python -c "
import requests
response = requests.get('https://www1.cityoforlando.net/opd/activecalls/activecadpolice.xml')
content = response.content.decode('utf-8-sig', errors='replace')
print(content[:500])
"
```

If this fails, the feed URL or network is the problem.

### Manual Feed Fetch and Parse

```bash
# Download the feed
Invoke-WebRequest -Uri "https://www1.cityoforlando.net/opd/activecalls/activecadpolice.xml" -OutFile feed.xml

# View it
type feed.xml | more
```

Look for:
- `<INCIDENT>` tags (incidents)
- Fields like `<IncidentNumber>`, `<IncidentLocation>`
- Any parsing errors in the XML

---

## Getting Help

### If you still can't fix it:

1. **Check all documentation**:
   - README.md - General usage
   - SETUP.md - Setup help
   - CONFIG_REFERENCE.md - Configuration
   - This file - Troubleshooting

2. **Enable DEBUG logging** and run bot:
   ```bash
   python opd_slack_bot.py > debug.log 2>&1
   ```

3. **Share these details** (if asking for support):
   - The error message (full text)
   - Your debug.log file
   - What you tried to fix it
   - Your Windows version
   - Your Python version (`python --version`)

---

## Common Error Messages Reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `ModuleNotFoundError: No module named 'requests'` | Package not installed | Run `pip install requests` |
| `Failed to fetch feed: ...` | Can't reach OPD server | Check internet, try again |
| `No incidents found in feed` | Feed is empty or unparseable | Check feed URL, OPD server status |
| `Failed to post to Slack: 403` | Webhook invalid or expired | Generate new webhook |
| `SLACK_WEBHOOK_URL environment variable is not set` | Environment var not found | Set `SLACK_WEBHOOK_URL` env var |
| `RequestException: ...` | Network error | Check internet connection |
| `json.JSONDecodeError: ...` | seen_incidents.json is corrupted | Delete and recreate |

---

**Last Updated**: January 2025
**Compatible**: Windows 10+, Python 3.7+
