"""
log_parser.py — regex-based parsers for two common log formats.

1. Apache/Nginx "combined" access log format:
   127.0.0.1 - - [29/Jul/2026:10:15:32 +0000] "GET /index.html HTTP/1.1" 200 1024 "-" "Mozilla/5.0"

2. Generic application log format:
   2026-07-29 10:15:32,123 ERROR [auth.module] Login failed: invalid token

Each parser returns a dict of extracted fields, or None if the line
doesn't match (malformed/unrecognized lines are skipped, not crashed on
— real-world logs always have a few garbage lines).
"""

import re
from datetime import datetime

APACHE_LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" '
    r'(?P<status>\d{3}) (?P<size>\S+) '
    r'"(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"'
)

APP_LOG_PATTERN = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:,\d+)?\s+'
    r'(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+'
    r'(?:\[(?P<module>[^\]]+)\]\s+)?'
    r'(?P<message>.*)$'
)


def parse_apache_line(line: str) -> dict | None:
    match = APACHE_LOG_PATTERN.match(line.strip())
    if not match:
        return None

    data = match.groupdict()
    try:
        # Strip timezone offset (e.g. "+0000") before parsing the timestamp.
        ts_without_tz = data["timestamp"].rsplit(" ", 1)[0]
        data["parsed_timestamp"] = datetime.strptime(ts_without_tz, "%d/%b/%Y:%H:%M:%S")
    except ValueError:
        data["parsed_timestamp"] = None

    data["status"] = int(data["status"])
    data["size"] = int(data["size"]) if data["size"].isdigit() else 0
    return data


def parse_app_line(line: str) -> dict | None:
    match = APP_LOG_PATTERN.match(line.strip())
    if not match:
        return None

    data = match.groupdict()
    try:
        data["parsed_timestamp"] = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        data["parsed_timestamp"] = None

    return data
