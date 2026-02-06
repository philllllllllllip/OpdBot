#!/usr/bin/env python3
"""
Orlando Police Department Active Calls Slack Alert Bot
Monitors the OPD active calls XML feed and posts alerts to Slack for matching incidents.
"""

import requests
import json
import time
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from urllib.parse import quote

try:
    import xmltodict
except ImportError:
    xmltodict = None

try:
    import xml.etree.ElementTree as ET
except ImportError:
    ET = None

# ============================================================================
# CONFIGURATION
# ============================================================================

# Feed URL
FEED_URL = "https://www1.cityoforlando.net/opd/activecalls/activecadpolice.xml"

# Polling interval (seconds)
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))

# Slack webhook (optional)
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Watch zone corridor keywords (location must contain ONE of these)
CORRIDOR_KEYWORDS = [
    "MILLS",
    "ORANGE",
    "ORLANDO AVE",
    "17/92",
    "US 17",
    "LEE RD",
    "VIRGINIA DR",
    "HORATIO",
]

# Seen incidents file (for deduplication)
SEEN_INCIDENTS_FILE = Path(__file__).parent / "seen_incidents.json"

# Request timeout
REQUEST_TIMEOUT = 10

# User-Agent (browser-like)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def load_seen_incidents() -> Set[str]:
    """Load set of already-seen incident numbers from JSON file."""
    if SEEN_INCIDENTS_FILE.exists():
        try:
            with open(SEEN_INCIDENTS_FILE, "r") as f:
                data = json.load(f)
                return set(data.get("incidents", []))
        except Exception as e:
            logger.warning(f"Failed to load seen incidents: {e}")
            return set()
    return set()


def save_seen_incidents(incident_numbers: Set[str]) -> None:
    """Save seen incident numbers to JSON file."""
    try:
        with open(SEEN_INCIDENTS_FILE, "w") as f:
            json.dump({"incidents": sorted(list(incident_numbers))}, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save seen incidents: {e}")


def location_matches_corridor(location: str) -> bool:
    """Check if location contains any corridor keyword (case-insensitive)."""
    if not location:
        return False
    location_upper = location.upper()
    for keyword in CORRIDOR_KEYWORDS:
        if keyword.upper() in location_upper:
            return True
    return False


def fetch_feed() -> Optional[str]:
    """Fetch the OPD active calls feed, handling UTF-8 BOM."""
    try:
        response = requests.get(
            FEED_URL,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        # Decode content with UTF-8 BOM handling
        content = response.content.decode("utf-8-sig", errors="replace")
        return content
    except requests.RequestException as e:
        logger.error(f"Failed to fetch feed: {e}")
        return None


def parse_feed_xmltodict(xml_content: str) -> Optional[List[Dict]]:
    """Parse feed using xmltodict (preferred)."""
    if xmltodict is None:
        return None
    try:
        data = xmltodict.parse(xml_content)
        # Navigate the structure to find incidents
        # Structure typically: root -> CAD_INCIDENTS -> INCIDENT or similar
        if data is None:
            return None

        # Try to find incidents list
        for key in data:
            if isinstance(data[key], dict):
                # Check if this dict contains INCIDENT(s)
                for sub_key in data[key]:
                    if "INCIDENT" in sub_key.upper():
                        incidents = data[key][sub_key]
                        # Normalize to list
                        if isinstance(incidents, dict):
                            return [incidents]
                        elif isinstance(incidents, list):
                            return incidents
        return None
    except Exception as e:
        logger.warning(f"xmltodict parsing failed: {e}")
        return None


def parse_feed_elementtree(xml_content: str) -> Optional[List[Dict]]:
    """Parse feed using ElementTree (fallback)."""
    try:
        root = ET.fromstring(xml_content)
        incidents = []

        # Recursively find all elements that look like incidents
        for elem in root.iter():
            if "INCIDENT" in elem.tag.upper():
                incident = {}
                for child in elem:
                    tag = child.tag
                    # Remove namespace if present
                    if "}" in tag:
                        tag = tag.split("}")[-1]
                    incident[tag] = child.text
                if incident:
                    incidents.append(incident)
        return incidents if incidents else None
    except Exception as e:
        logger.warning(f"ElementTree parsing failed: {e}")
        return None


def parse_feed(xml_content: str) -> Optional[List[Dict]]:
    """Parse XML feed, trying xmltodict first, then ElementTree."""
    incidents = parse_feed_xmltodict(xml_content)
    if incidents:
        return incidents
    incidents = parse_feed_elementtree(xml_content)
    return incidents


def post_to_slack(incident: Dict) -> bool:
    """Post incident alert to Slack."""
    if not SLACK_WEBHOOK_URL:
        logger.info(f"Slack webhook not configured; skipping post for {incident.get('IncidentNumber', 'unknown')}")
        return True

    try:
        incident_number = incident.get("IncidentNumber", "N/A")
        call_type = incident.get("CallType", "N/A")
        date_time = incident.get("DateTime", "N/A")
        location = incident.get("IncidentLocation", "N/A")
        district = incident.get("District", "N/A")

        # Build Google Maps link
        maps_url = f"https://www.google.com/maps/search/?api=1&query={quote(location)}"

        # Build Slack message
        message = {
            "text": f"🚨 New OPD Call: {incident_number}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🚨 New OPD Active Call*\n\n"
                        f"*Incident:* {incident_number}\n"
                        f"*Type:* {call_type}\n"
                        f"*Time:* {date_time}\n"
                        f"*Location:* {location}\n"
                        f"*District:* {district}",
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View on Maps"},
                            "url": maps_url,
                            "style": "primary",
                        }
                    ],
                },
            ],
        }

        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=message,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        logger.info(f"Posted to Slack: {incident_number}")
        return True
    except Exception as e:
        logger.error(f"Failed to post to Slack: {e}")
        return False


def process_feed(current_seen: Set[str]) -> None:
    """Fetch, parse, and process the feed."""
    xml_content = fetch_feed()
    if not xml_content:
        return

    incidents = parse_feed(xml_content)
    if not incidents:
        logger.warning("No incidents found in feed")
        return

    logger.info(f"Found {len(incidents)} incidents in feed")

    new_incidents = []
    for incident in incidents:
        if not isinstance(incident, dict):
            continue

        incident_number = incident.get("IncidentNumber") or incident.get("IncidentNum")
        if not incident_number:
            logger.debug(f"Skipping incident with no number: {incident}")
            continue

        # Check if we've seen this incident before
        if incident_number in current_seen:
            logger.debug(f"Already seen incident {incident_number}")
            continue

        # Check if location matches our corridor
        location = incident.get("IncidentLocation", "")
        if not location_matches_corridor(location):
            logger.debug(f"Incident {incident_number} location '{location}' does not match corridor")
            continue

        logger.info(f"New matching incident found: {incident_number}")
        new_incidents.append(incident)
        current_seen.add(incident_number)

    # Post new incidents to Slack
    for incident in new_incidents:
        post_to_slack(incident)

    # Save updated seen incidents
    if new_incidents:
        save_seen_incidents(current_seen)


def test_slack_connection() -> None:
    """Test Slack webhook connection."""
    logger.info("=" * 70)
    logger.info("Testing Slack Connection")
    logger.info("=" * 70)
    
    if not SLACK_WEBHOOK_URL:
        logger.error("ERROR: SLACK_WEBHOOK_URL environment variable not set")
        sys.exit(1)
    
    logger.info(f"Webhook URL: {SLACK_WEBHOOK_URL[:50]}...")
    
    test_message = {
        "text": "🔧 OPD Alert Bot - Test Message",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔧 OPD Alert Bot Test*\n\n"
                            "*Status:* ✅ Running\n"
                            "*Time:* " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n"
                            "Bot is connected and able to post messages to Slack!",
                },
            }
        ]
    }
    
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=test_message,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        logger.info("✅ SUCCESS: Test message posted to Slack!")
        logger.info("=" * 70)
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        logger.error("=" * 70)
        sys.exit(1)


def main() -> None:
    """Main bot loop."""
    logger.info("=" * 70)
    logger.info("Orlando Police Department Active Calls Slack Alert Bot")
    logger.info("=" * 70)
    logger.info(f"Feed URL: {FEED_URL}")
    logger.info(f"Poll interval: {POLL_INTERVAL} seconds")
    logger.info(f"Slack webhook configured: {bool(SLACK_WEBHOOK_URL)}")
    logger.info(f"Watch zone keywords: {', '.join(CORRIDOR_KEYWORDS)}")
    logger.info(f"Seen incidents file: {SEEN_INCIDENTS_FILE}")
    logger.info("=" * 70)

    current_seen = load_seen_incidents()
    logger.info(f"Loaded {len(current_seen)} previously seen incidents")

    try:
        while True:
            logger.info(f"Polling feed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            process_feed(current_seen)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Bot shutting down (user interrupt)")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Check for command-line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "test":
            test_slack_connection()
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Usage: python opd_slack_bot.py [test]")
            sys.exit(1)
    else:
        main()
