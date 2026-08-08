"""
Generates realistic-looking sample log files so you can try the analyzer
on something substantial right away, including a demonstration of it
handling a genuinely large file without slowing to a crawl.

Usage:
    python generate_sample_logs.py
    python analyzer.py sample_access.log --format apache
    python analyzer.py sample_app.log --format app
"""

import random
from datetime import datetime, timedelta

IPS = [f"192.168.1.{i}" for i in range(1, 30)] + [f"10.0.0.{i}" for i in range(1, 15)]
PATHS = ["/", "/index.html", "/about", "/products", "/products/42", "/api/users",
         "/api/orders", "/login", "/logout", "/checkout", "/static/style.css",
         "/images/logo.png", "/favicon.ico"]
METHODS = ["GET", "GET", "GET", "GET", "POST", "POST", "PUT", "DELETE"]
STATUS_CODES = [200] * 20 + [304] * 5 + [404] * 3 + [500] * 1 + [301] * 2 + [403] * 1
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "curl/8.4.0",
]

APP_MODULES = ["auth", "payments", "orders.service", "api.gateway", "database"]
APP_MESSAGES = {
    "INFO": ["Request completed successfully", "User logged in", "Cache refreshed",
              "Scheduled job started", "Health check passed"],
    "DEBUG": ["Entering function process_order", "Cache miss for key user:1234",
              "Retrying connection (attempt 1)"],
    "WARNING": ["Response time exceeded 2s threshold", "Deprecated API endpoint used",
                 "Retry limit approaching"],
    "ERROR": ["Database connection timeout", "Failed to process payment: card declined",
               "Unhandled exception in request handler", "External API returned 503"],
    "CRITICAL": ["Database connection pool exhausted", "Service unavailable - out of memory"],
}
LEVEL_WEIGHTS = ["INFO"] * 60 + ["DEBUG"] * 20 + ["WARNING"] * 12 + ["ERROR"] * 7 + ["CRITICAL"] * 1


def generate_apache_log(path: str, num_lines: int = 20000) -> None:
    start_time = datetime(2026, 7, 1, 0, 0, 0)
    with open(path, "w", encoding="utf-8") as f:
        for i in range(num_lines):
            ts = start_time + timedelta(seconds=random.randint(0, 30 * 24 * 3600))
            ip = random.choice(IPS)
            method = random.choice(METHODS)
            path_ = random.choice(PATHS)
            status = random.choice(STATUS_CODES)
            size = random.randint(200, 50000)
            ua = random.choice(USER_AGENTS)
            timestamp_str = ts.strftime("%d/%b/%Y:%H:%M:%S +0000")
            f.write(f'{ip} - - [{timestamp_str}] "{method} {path_} HTTP/1.1" {status} {size} "-" "{ua}"\n')

        # Sprinkle in a few malformed lines, since real logs always have some.
        f.write("this is not a valid log line\n")
        f.write("### TRUNCATED ###\n")

    print(f"Generated {num_lines:,} lines (+2 malformed) -> {path}")


def generate_app_log(path: str, num_lines: int = 20000) -> None:
    start_time = datetime(2026, 7, 1, 0, 0, 0)
    with open(path, "w", encoding="utf-8") as f:
        for i in range(num_lines):
            ts = start_time + timedelta(seconds=random.randint(0, 30 * 24 * 3600))
            level = random.choice(LEVEL_WEIGHTS)
            module = random.choice(APP_MODULES)
            message = random.choice(APP_MESSAGES[level])
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts_str},{random.randint(0,999):03d} {level} [{module}] {message}\n")

        f.write("garbage line that will not parse\n")

    print(f"Generated {num_lines:,} lines (+1 malformed) -> {path}")


if __name__ == "__main__":
    generate_apache_log("sample_access.log", num_lines=20000)
    generate_app_log("sample_app.log", num_lines=20000)
    print("\nTry:")
    print("  python analyzer.py sample_access.log --format apache")
    print("  python analyzer.py sample_app.log --format app")
