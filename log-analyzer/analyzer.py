"""
Log Analyzer CLI
------------------
Reads a log file line-by-line (constant memory, works on huge files),
parses it with regex, aggregates stats with collections.Counter /
defaultdict, and prints a readable report.

Usage:
    python analyzer.py access.log --format apache
    python analyzer.py app.log --format app --top 10
    python analyzer.py access.log --format apache --output report.txt
    python analyzer.py access.log --format apache --json stats.json

Author: (your name) - Python Basics Project 5
"""

import argparse
import sys
from pathlib import Path

from log_analyzer import analyze_apache_log, analyze_app_log
from report import build_apache_report, build_app_report, stats_to_json


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze log files and generate reports.")
    parser.add_argument("logfile", type=str, help="Path to the log file to analyze")
    parser.add_argument("--format", choices=["apache", "app"], required=True,
                         help="Log format: 'apache' for web server access logs, "
                              "'app' for generic application logs (timestamp + level + message)")
    parser.add_argument("--top", type=int, default=5, help="Number of top items to show in the report (default: 5)")
    parser.add_argument("--output", type=str, default=None, help="Save the text report to this file")
    parser.add_argument("--json", type=str, default=None, help="Save raw stats as JSON to this file")
    return parser.parse_args()


def main():
    args = parse_args()
    log_path = Path(args.logfile)

    if not log_path.exists():
        print(f"Error: file not found: {log_path}", file=sys.stderr)
        sys.exit(1)

    if args.format == "apache":
        stats = analyze_apache_log(log_path)
        report_text = build_apache_report(stats, top_n=args.top)
    else:
        stats = analyze_app_log(log_path)
        report_text = build_app_report(stats, top_n=args.top)

    print(report_text)

    if args.output:
        Path(args.output).write_text(report_text, encoding="utf-8")
        print(f"\nReport saved to {args.output}")

    if args.json:
        Path(args.json).write_text(stats_to_json(stats), encoding="utf-8")
        print(f"Raw stats saved to {args.json}")


if __name__ == "__main__":
    main()
