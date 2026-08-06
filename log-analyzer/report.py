"""
report.py — turns the stats dicts from log_analyzer.py into a clean,
readable text report (console or file), plus a simple ASCII bar chart
for status codes / log levels — a nice visual touch for a portfolio demo.
"""

import json
from collections import defaultdict

MAX_HOUR_ROWS = 48  # beyond this, collapse to daily totals so the report stays readable


def _bar(count: int, max_count: int, width: int = 30) -> str:
    if max_count == 0:
        return ""
    filled = int((count / max_count) * width)
    return "#" * filled


def build_apache_report(stats: dict, top_n: int = 5) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  ACCESS LOG ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append(f"Total requests parsed : {stats['total_requests']:,}")
    lines.append(f"Unparseable lines     : {stats['unparseable_lines']:,}")
    lines.append(f"Total bytes served    : {stats['total_bytes']:,}")
    lines.append(f"Error rate (4xx/5xx)  : {stats['error_rate']}%  ({stats['error_count']:,} errors)")

    lines.append("\n--- Status Code Breakdown ---")
    max_count = max(stats["status_counts"].values(), default=0)
    for status, count in sorted(stats["status_counts"].items()):
        lines.append(f"  {status}  {count:>7,}  {_bar(count, max_count)}")

    lines.append(f"\n--- Top {top_n} Requested Endpoints ---")
    for path, count in stats["endpoint_counts"].most_common(top_n):
        lines.append(f"  {count:>7,}  {path}")

    lines.append(f"\n--- Top {top_n} IP Addresses ---")
    for ip, count in stats["ip_counts"].most_common(top_n):
        lines.append(f"  {count:>7,}  {ip}")

    lines.append("\n--- HTTP Methods ---")
    for method, count in stats["method_counts"].most_common():
        lines.append(f"  {method:<8}{count:>7,}")

    lines.append(_build_time_series_section(stats["requests_per_hour"], "Requests"))

    lines.append("=" * 60)
    return "\n".join(lines)


def _build_time_series_section(per_hour: dict, label: str) -> str:
    """
    Render a per-hour breakdown, or collapse to per-day totals if there
    are too many hourly buckets to display readably (e.g. a log spanning
    weeks or months).
    """
    if not per_hour:
        return ""

    if len(per_hour) <= MAX_HOUR_ROWS:
        rows = [f"\n--- {label} Per Hour ---"]
        for hour, count in per_hour.items():
            rows.append(f"  {hour}   {count:>6,}")
        return "\n".join(rows)

    daily_totals = defaultdict(int)
    for hour_key, count in per_hour.items():
        day_key = hour_key.split(" ")[0]  # "2026-07-01 14:00" -> "2026-07-01"
        daily_totals[day_key] += count

    rows = [f"\n--- {label} Per Day ---",
            f"(spans {len(per_hour)} hourly buckets — showing daily totals for readability)"]
    for day, count in sorted(daily_totals.items()):
        rows.append(f"  {day}   {count:>6,}")
    return "\n".join(rows)


def build_app_report(stats: dict, top_n: int = 5) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  APPLICATION LOG ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append(f"Total lines parsed   : {stats['total_lines']:,}")
    lines.append(f"Unparseable lines    : {stats['unparseable_lines']:,}")
    lines.append(f"Error rate           : {stats['error_rate']}%  ({stats['error_count']:,} errors)")

    lines.append("\n--- Log Level Breakdown ---")
    max_count = max(stats["level_counts"].values(), default=0)
    for level, count in stats["level_counts"].most_common():
        lines.append(f"  {level:<10}{count:>7,}  {_bar(count, max_count)}")

    if stats["module_counts"]:
        lines.append(f"\n--- Top {top_n} Noisiest Modules ---")
        for module, count in stats["module_counts"].most_common(top_n):
            lines.append(f"  {count:>7,}  {module}")

    lines.append(_build_time_series_section(stats["messages_per_hour"], "Messages"))

    if stats["error_messages"]:
        lines.append(f"\n--- Most Recent {min(top_n, len(stats['error_messages']))} Error Messages ---")
        for msg in stats["error_messages"][-top_n:]:
            lines.append(f"  {msg}")

    lines.append("=" * 60)
    return "\n".join(lines)


def stats_to_json(stats: dict) -> str:
    """Convert a stats dict (which may contain Counter objects) to a JSON string."""
    serializable = {}
    for key, value in stats.items():
        if hasattr(value, "most_common"):  # it's a Counter
            serializable[key] = dict(value)
        else:
            serializable[key] = value
    return json.dumps(serializable, indent=2, default=str)
