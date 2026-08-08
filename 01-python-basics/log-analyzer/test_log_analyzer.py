"""
Unit tests for log_parser.py and log_analyzer.py
Run with:  python -m unittest test_log_analyzer.py -v
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from log_analyzer import analyze_apache_log, analyze_app_log
from log_parser import parse_apache_line, parse_app_line


class TestParseApacheLine(unittest.TestCase):
    def test_valid_line_parses_all_fields(self):
        line = '192.168.1.1 - - [29/Jul/2026:10:15:32 +0000] "GET /index.html HTTP/1.1" 200 1024 "-" "Mozilla/5.0"'
        result = parse_apache_line(line)
        self.assertIsNotNone(result)
        self.assertEqual(result["ip"], "192.168.1.1")
        self.assertEqual(result["method"], "GET")
        self.assertEqual(result["path"], "/index.html")
        self.assertEqual(result["status"], 200)
        self.assertEqual(result["size"], 1024)

    def test_invalid_line_returns_none(self):
        self.assertIsNone(parse_apache_line("this is not a log line"))

    def test_timestamp_is_parsed_to_datetime(self):
        line = '10.0.0.5 - - [01/Jan/2026:00:00:00 +0000] "GET / HTTP/1.1" 200 500 "-" "curl/8.0"'
        result = parse_apache_line(line)
        self.assertEqual(result["parsed_timestamp"].year, 2026)
        self.assertEqual(result["parsed_timestamp"].hour, 0)

    def test_dash_size_becomes_zero(self):
        line = '10.0.0.5 - - [01/Jan/2026:00:00:00 +0000] "GET / HTTP/1.1" 304 - "-" "curl/8.0"'
        result = parse_apache_line(line)
        self.assertEqual(result["size"], 0)


class TestParseAppLine(unittest.TestCase):
    def test_valid_line_with_module(self):
        line = "2026-07-29 10:15:32,123 ERROR [auth] Login failed"
        result = parse_app_line(line)
        self.assertIsNotNone(result)
        self.assertEqual(result["level"], "ERROR")
        self.assertEqual(result["module"], "auth")
        self.assertEqual(result["message"], "Login failed")

    def test_valid_line_without_module(self):
        line = "2026-07-29 10:15:32 INFO Server started"
        result = parse_app_line(line)
        self.assertIsNotNone(result)
        self.assertIsNone(result["module"])
        self.assertEqual(result["message"], "Server started")

    def test_invalid_line_returns_none(self):
        self.assertIsNone(parse_app_line("not a log line at all"))

    def test_unknown_level_returns_none(self):
        self.assertIsNone(parse_app_line("2026-07-29 10:15:32 TRACE Something"))


class TestAnalyzeApacheLog(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.log_file = self.tmp_dir / "access.log"
        lines = [
            '192.168.1.1 - - [29/Jul/2026:10:00:00 +0000] "GET / HTTP/1.1" 200 500 "-" "curl/8.0"',
            '192.168.1.1 - - [29/Jul/2026:10:05:00 +0000] "GET /about HTTP/1.1" 200 700 "-" "curl/8.0"',
            '192.168.1.2 - - [29/Jul/2026:10:10:00 +0000] "GET / HTTP/1.1" 404 200 "-" "curl/8.0"',
            '192.168.1.2 - - [29/Jul/2026:11:00:00 +0000] "POST /login HTTP/1.1" 500 100 "-" "curl/8.0"',
            "this line is garbage and will not parse",
        ]
        self.log_file.write_text("\n".join(lines))

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_total_requests_and_unparseable_count(self):
        stats = analyze_apache_log(self.log_file)
        self.assertEqual(stats["total_requests"], 4)
        self.assertEqual(stats["unparseable_lines"], 1)

    def test_status_counts(self):
        stats = analyze_apache_log(self.log_file)
        self.assertEqual(stats["status_counts"][200], 2)
        self.assertEqual(stats["status_counts"][404], 1)
        self.assertEqual(stats["status_counts"][500], 1)

    def test_ip_counts(self):
        stats = analyze_apache_log(self.log_file)
        self.assertEqual(stats["ip_counts"]["192.168.1.1"], 2)
        self.assertEqual(stats["ip_counts"]["192.168.1.2"], 2)

    def test_error_rate_calculation(self):
        stats = analyze_apache_log(self.log_file)
        # 2 errors (404 + 500) out of 4 total = 50%
        self.assertEqual(stats["error_rate"], 50.0)

    def test_requests_per_hour_buckets(self):
        stats = analyze_apache_log(self.log_file)
        self.assertEqual(stats["requests_per_hour"]["2026-07-29 10:00"], 3)
        self.assertEqual(stats["requests_per_hour"]["2026-07-29 11:00"], 1)

    def test_top_endpoints(self):
        stats = analyze_apache_log(self.log_file)
        top = stats["endpoint_counts"].most_common(1)
        self.assertEqual(top[0], ("/", 2))


class TestAnalyzeAppLog(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.log_file = self.tmp_dir / "app.log"
        lines = [
            "2026-07-29 10:00:00 INFO [auth] User logged in",
            "2026-07-29 10:05:00 ERROR [payments] Card declined",
            "2026-07-29 10:10:00 WARNING [api] Slow response",
            "2026-07-29 11:00:00 CRITICAL [database] Connection pool exhausted",
            "garbage that does not match",
        ]
        self.log_file.write_text("\n".join(lines))

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_total_lines_and_unparseable(self):
        stats = analyze_app_log(self.log_file)
        self.assertEqual(stats["total_lines"], 4)
        self.assertEqual(stats["unparseable_lines"], 1)

    def test_level_counts(self):
        stats = analyze_app_log(self.log_file)
        self.assertEqual(stats["level_counts"]["INFO"], 1)
        self.assertEqual(stats["level_counts"]["ERROR"], 1)
        self.assertEqual(stats["level_counts"]["CRITICAL"], 1)

    def test_error_count_includes_critical(self):
        stats = analyze_app_log(self.log_file)
        self.assertEqual(stats["error_count"], 2)  # 1 ERROR + 1 CRITICAL

    def test_error_messages_collected(self):
        stats = analyze_app_log(self.log_file)
        self.assertEqual(len(stats["error_messages"]), 2)
        self.assertTrue(any("Card declined" in m for m in stats["error_messages"]))


if __name__ == "__main__":
    unittest.main()
