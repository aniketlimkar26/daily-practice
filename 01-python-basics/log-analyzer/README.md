# 📊 Log Analyzer

**Roadmap stage:** Python Basics — Project 5
**Skills practiced:** regex, streaming file handling, `collections.Counter` / `defaultdict`, report generation

A command-line tool that reads log files and generates readable analysis
reports — request patterns, error rates, top endpoints/IPs, log level
breakdowns, and more. Built to handle **large files efficiently**, which
is exactly the kind of practical, real-world tool that stands out on a
resume.

## ⚙️ Why This Scales to Huge Files

Every analysis function reads the file **line-by-line**:
```python
with open(file_path) as f:
    for line in f:
        ...
```
This means memory usage stays constant regardless of file size — a
50 MB log and a 50 GB log both use roughly the same tiny amount of RAM,
because only one line is ever held in memory at a time. This is the
difference between a script that only works on toy files and a tool
that would actually survive in production.

## ✨ Features

- **Two log formats supported:**
  - `apache` — standard Apache/Nginx combined access log format
  - `app` — generic application logs (`timestamp LEVEL [module] message`)
- **Apache report includes:** status code breakdown (with ASCII bar chart),
  top endpoints, top IPs, HTTP method counts, error rate, requests per
  hour/day
- **App log report includes:** log level breakdown, noisiest modules,
  error rate, recent error messages, messages per hour/day
- **Auto-collapsing time series:** if a log spans many hours, the report
  automatically switches from hourly to daily totals so it stays readable
- **Malformed-line tolerant:** unparseable lines are counted and skipped,
  never crash the tool (real logs always have a few garbage lines)
- **Export options:** save the report as text (`--output`) or the raw
  stats as JSON (`--json`)

## 📂 Project Structure

```
log-analyzer/
├── analyzer.py               # CLI entry point
├── log_parser.py              # regex parsers for both log formats
├── log_analyzer.py            # streaming analysis logic (Counter/defaultdict)
├── report.py                   # formats stats into readable reports
├── generate_sample_logs.py    # generates 20,000-line sample log files
├── test_log_analyzer.py       # unit tests (18 tests)
└── README.md
```

## 🚀 Usage

### 1. Generate sample logs to try it on

```bash
python generate_sample_logs.py
```
This creates `sample_access.log` and `sample_app.log`, each with 20,000
realistic lines (plus a couple of deliberately malformed lines, since
real logs always have some).

### 2. Analyze an access log

```bash
python analyzer.py sample_access.log --format apache
python analyzer.py sample_access.log --format apache --top 10
```

### 3. Analyze an application log

```bash
python analyzer.py sample_app.log --format app
```

### 4. Save the report / export raw stats

```bash
python analyzer.py sample_access.log --format apache --output report.txt
python analyzer.py sample_access.log --format apache --json stats.json
```

## 🧪 Running Tests

```bash
python -m unittest test_log_analyzer.py -v
```

## 🧠 What I Learned

- Writing regex patterns with **named groups** (`(?P<name>...)`) to
  extract structured data from unstructured text
- The critical difference between reading a whole file into memory
  (`f.read()`) vs. streaming it line-by-line — and why that choice
  determines whether a tool can handle production-scale data
- Using `collections.Counter` for frequency counting (status codes, IPs,
  endpoints) and `collections.defaultdict` for time-bucketed aggregation,
  instead of manually managing dictionaries with `if key not in dict`
  checks everywhere
- Designing for messy real-world input: logs always have a few lines
  that don't match the expected format, and a good tool degrades
  gracefully (counts them, doesn't crash) instead of failing outright
- UX detail: a report with 720 rows of hourly data is useless — auto-
  collapsing to daily totals when there's too much data is a small
  design decision that makes the tool actually usable

## 🔮 Possible Future Improvements

- [ ] Support for JSON-formatted logs (common in modern cloud apps)
- [ ] Detect and flag anomalies (e.g. sudden spike in errors)
- [ ] Multi-file analysis (combine several rotated log files into one report)

---
📅 Part of my [Python Basics → Production Project roadmap](../README.md).
