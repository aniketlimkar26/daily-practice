# 💰 Expense Tracker CLI

**Roadmap stage:** Python Basics — Project 3
**Skills practiced:** JSON file storage, CRUD design, `argparse` subcommands, data filtering/aggregation, `unittest`

A command-line expense tracker with full CRUD (Create, Read, Update,
Delete), category and date-range filtering, and a spending summary —
all backed by a local JSON file. No database required (yet — that's a
future roadmap stage!).

## ✨ Features

- **Add** expenses with amount, category, description, and date
- **List** all expenses, or filter by category and/or date range
- **Update** any field of an existing expense by ID
- **Delete** an expense by ID
- **Summary** — total spend and a per-category breakdown, filterable by
  category or month
- Data persisted in a human-readable `expenses.json` file
- Auto-incrementing IDs, sorted output, input validation on dates

## 📂 Project Structure

```
expense-tracker-cli/
├── tracker.py            # main CLI tool (add/list/update/delete/summary)
├── test_tracker.py       # unit tests (17 tests)
├── seed_demo_data.py     # seeds sample expenses to try the tool immediately
└── README.md
```

## 🚀 Usage

### 1. Seed some demo data first (recommended)

```bash
python seed_demo_data.py
python tracker.py list
python tracker.py summary
```

### 2. Add expenses

```bash
python tracker.py add --amount 12.50 --category Food --description "Lunch"
python tracker.py add --amount 45 --category Transport --date 2026-07-05
```
(`--date` defaults to today if omitted)

### 3. List / filter

```bash
python tracker.py list
python tracker.py list --category Food
python tracker.py list --start-date 2026-07-01 --end-date 2026-07-31
```

### 4. Update / delete

```bash
python tracker.py update 3 --amount 9.50 --description "Coffee + tip"
python tracker.py delete 2
```

### 5. Summary

```bash
python tracker.py summary
python tracker.py summary --category Food
python tracker.py summary --month 2026-07
```

### Using a custom data file
Every command accepts `--file` to point at a different JSON file, e.g.
`python tracker.py --file work_expenses.json add --amount 5 --category Office`

## 🧪 Running Tests

```bash
python -m unittest test_tracker.py -v
```

## 🧠 What I Learned

- Reading and writing structured data with the `json` module
- Designing a proper **CRUD** interface (Create/Read/Update/Delete) —
  the same core pattern behind almost every backend API you'll ever build
- Building a **multi-command CLI** with `argparse` subparsers (`add`,
  `list`, `update`, `delete`, `summary` each with their own arguments)
- Data aggregation logic (grouping and summing by category/month) —
  the same mental model used later for SQL `GROUP BY` queries
- Defensive coding: validating dates, handling missing IDs, handling a
  corrupted/missing JSON file gracefully

## 🔮 Possible Future Improvements

- [ ] Export summary to CSV
- [ ] Monthly budget limits with warnings when exceeded
- [ ] Swap the JSON file for a real database (this is exactly what the
      **Database** stage of the roadmap will cover!)

---
📅 Part of my [Python Basics → Production Project roadmap](../README.md).
