"""
log_analyzer.py — streaming log analysis.

IMPORTANT DESIGN NOTE: every analysis function reads the file line-by-line
using a simple `for line in f:` loop. This means memory usage stays
constant no matter how large the file is — a 50 MB log file and a 50 GB
log file both use the same tiny amount of RAM, because we never load
more than one line into memory at once. This is the difference between
a script that works on toy files and a tool that works in production.
"""

from collections import Counter, defaultdict
from pathlib import Path

from log_parser import parse_apache_line, parse_app_line


def analyze_apache_log(file_path: Path) -> dict:
    total_requests = 0
    unparseable = 0
    status_counts = Counter()
    ip_counts = Counter()
    endpoint_counts = Counter()
    method_counts = Counter()
    requests_per_hour = defaultdict(int)
    total_bytes = 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            record = parse_apache_line(line)
            if record is None:
                unparseable += 1
                continue

            total_requests += 1
            status_counts[record["status"]] += 1
            ip_counts[record["ip"]] += 1
            endpoint_counts[record["path"]] += 1
            method_counts[record["method"]] += 1
            total_bytes += record["size"]

            if record["parsed_timestamp"]:
                hour_bucket = record["parsed_timestamp"].strftime("%Y-%m-%d %H:00")
                requests_per_hour[hour_bucket] += 1

    error_count = sum(count for status, count in status_counts.items() if status >= 400)

    return {
        "format": "apache",
        "total_requests": total_requests,
        "unparseable_lines": unparseable,
        "status_counts": status_counts,
        "ip_counts": ip_counts,
        "endpoint_counts": endpoint_counts,
        "method_counts": method_counts,
        "requests_per_hour": dict(sorted(requests_per_hour.items())),
        "total_bytes": total_bytes,
        "error_count": error_count,
        "error_rate": round(error_count / total_requests * 100, 2) if total_requests else 0.0,
    }


def analyze_app_log(file_path: Path) -> dict:
    total_lines = 0
    unparseable = 0
    level_counts = Counter()
    module_counts = Counter()
    messages_per_hour = defaultdict(int)
    error_messages = []  # keep the actual ERROR/CRITICAL messages for the report

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            record = parse_app_line(line)
            if record is None:
                unparseable += 1
                continue

            total_lines += 1
            level_counts[record["level"]] += 1
            if record["module"]:
                module_counts[record["module"]] += 1

            if record["level"] in ("ERROR", "CRITICAL"):
                error_messages.append(f"[{record['timestamp']}] {record['message']}")

            if record["parsed_timestamp"]:
                hour_bucket = record["parsed_timestamp"].strftime("%Y-%m-%d %H:00")
                messages_per_hour[hour_bucket] += 1

    error_count = level_counts["ERROR"] + level_counts["CRITICAL"]

    return {
        "format": "app",
        "total_lines": total_lines,
        "unparseable_lines": unparseable,
        "level_counts": level_counts,
        "module_counts": module_counts,
        "messages_per_hour": dict(sorted(messages_per_hour.items())),
        "error_messages": error_messages,
        "error_count": error_count,
        "error_rate": round(error_count / total_lines * 100, 2) if total_lines else 0.0,
    }
