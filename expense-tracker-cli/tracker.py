"""
Expense Tracker CLI
--------------------
A command-line expense tracker that stores data in a local JSON file
and supports full CRUD (Create, Read, Update, Delete) plus category
and date filtering and a spending summary.

Data is stored in expenses.json as a list of records:
    {
        "id": 1,
        "date": "2026-07-29",
        "category": "Food",
        "amount": 12.50,
        "description": "Lunch"
    }

Usage:
    python tracker.py add --amount 12.50 --category Food --description "Lunch"
    python tracker.py add --amount 45 --category Transport --date 2026-07-01

    python tracker.py list
    python tracker.py list --category Food
    python tracker.py list --start-date 2026-07-01 --end-date 2026-07-31

    python tracker.py update 1 --amount 15.00 --description "Lunch + coffee"
    python tracker.py delete 1

    python tracker.py summary
    python tracker.py summary --category Food
    python tracker.py summary --month 2026-07

Author: (your name) - Python Basics Project 3
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

DATA_FILE_NAME = "expenses.json"


# --------------------------------------------------------------------------
# Storage helpers
# --------------------------------------------------------------------------
def load_expenses(data_file: Path) -> list:
    """Load expenses from the JSON file. Returns an empty list if none exists."""
    if not data_file.exists():
        return []
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: {data_file} is corrupted or empty. Starting fresh.", file=sys.stderr)
        return []


def save_expenses(data_file: Path, expenses: list) -> None:
    """Save the full expense list back to the JSON file (pretty-printed)."""
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(expenses, f, indent=2)


def next_id(expenses: list) -> int:
    """Compute the next auto-increment ID."""
    if not expenses:
        return 1
    return max(e["id"] for e in expenses) + 1


def validate_date(date_str: str) -> str:
    """Validate a YYYY-MM-DD date string; raises ValueError if invalid."""
    datetime.strptime(date_str, "%Y-%m-%d")
    return date_str


# --------------------------------------------------------------------------
# CRUD operations
# --------------------------------------------------------------------------
def add_expense(data_file: Path, amount: float, category: str,
                 description: str, expense_date: str) -> dict:
    expenses = load_expenses(data_file)
    record = {
        "id": next_id(expenses),
        "date": expense_date,
        "category": category,
        "amount": round(amount, 2),
        "description": description,
    }
    expenses.append(record)
    save_expenses(data_file, expenses)
    return record


def list_expenses(data_file: Path, category: str = None,
                   start_date: str = None, end_date: str = None) -> list:
    expenses = load_expenses(data_file)

    if category:
        expenses = [e for e in expenses if e["category"].lower() == category.lower()]
    if start_date:
        expenses = [e for e in expenses if e["date"] >= start_date]
    if end_date:
        expenses = [e for e in expenses if e["date"] <= end_date]

    return sorted(expenses, key=lambda e: e["date"])


def update_expense(data_file: Path, expense_id: int, **fields) -> dict:
    expenses = load_expenses(data_file)
    for expense in expenses:
        if expense["id"] == expense_id:
            for key, value in fields.items():
                if value is not None:
                    expense[key] = round(value, 2) if key == "amount" else value
            save_expenses(data_file, expenses)
            return expense
    raise ValueError(f"No expense found with id {expense_id}")


def delete_expense(data_file: Path, expense_id: int) -> dict:
    expenses = load_expenses(data_file)
    for i, expense in enumerate(expenses):
        if expense["id"] == expense_id:
            removed = expenses.pop(i)
            save_expenses(data_file, expenses)
            return removed
    raise ValueError(f"No expense found with id {expense_id}")


def summarize(data_file: Path, category: str = None, month: str = None) -> dict:
    """Return total spend and a per-category breakdown, optionally filtered."""
    expenses = load_expenses(data_file)

    if category:
        expenses = [e for e in expenses if e["category"].lower() == category.lower()]
    if month:
        expenses = [e for e in expenses if e["date"].startswith(month)]

    total = round(sum(e["amount"] for e in expenses), 2)
    by_category = {}
    for e in expenses:
        by_category[e["category"]] = round(by_category.get(e["category"], 0) + e["amount"], 2)

    return {"total": total, "count": len(expenses), "by_category": by_category}


# --------------------------------------------------------------------------
# CLI presentation helpers
# --------------------------------------------------------------------------
def print_table(expenses: list) -> None:
    if not expenses:
        print("No expenses found.")
        return
    print(f"{'ID':<5}{'Date':<12}{'Category':<15}{'Amount':<10}Description")
    print("-" * 60)
    for e in expenses:
        print(f"{e['id']:<5}{e['date']:<12}{e['category']:<15}{e['amount']:<10.2f}{e['description']}")


def print_summary(summary: dict) -> None:
    print(f"Total spent: {summary['total']:.2f}  ({summary['count']} expense(s))")
    if summary["by_category"]:
        print("\nBy category:")
        for cat, amt in sorted(summary["by_category"].items(), key=lambda kv: -kv[1]):
            print(f"  {cat:<15}{amt:.2f}")


# --------------------------------------------------------------------------
# CLI argument parsing
# --------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Expense Tracker CLI")
    parser.add_argument("--file", type=str, default=DATA_FILE_NAME,
                         help="Path to the expenses JSON file (default: expenses.json)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_add = subparsers.add_parser("add", help="Add a new expense")
    p_add.add_argument("--amount", type=float, required=True)
    p_add.add_argument("--category", type=str, required=True)
    p_add.add_argument("--description", type=str, default="")
    p_add.add_argument("--date", type=str, default=None,
                        help="YYYY-MM-DD (defaults to today)")

    p_list = subparsers.add_parser("list", help="List expenses")
    p_list.add_argument("--category", type=str, default=None)
    p_list.add_argument("--start-date", type=str, default=None)
    p_list.add_argument("--end-date", type=str, default=None)

    p_update = subparsers.add_parser("update", help="Update an existing expense")
    p_update.add_argument("id", type=int)
    p_update.add_argument("--amount", type=float, default=None)
    p_update.add_argument("--category", type=str, default=None)
    p_update.add_argument("--description", type=str, default=None)
    p_update.add_argument("--date", type=str, default=None)

    p_delete = subparsers.add_parser("delete", help="Delete an expense")
    p_delete.add_argument("id", type=int)

    p_summary = subparsers.add_parser("summary", help="Show spending summary")
    p_summary.add_argument("--category", type=str, default=None)
    p_summary.add_argument("--month", type=str, default=None, help="YYYY-MM")

    return parser.parse_args()


def main():
    args = parse_args()
    data_file = Path(args.file)

    if args.command == "add":
        expense_date = args.date or date.today().isoformat()
        try:
            validate_date(expense_date)
        except ValueError:
            print(f"Error: invalid date '{expense_date}'. Use YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)
        record = add_expense(data_file, args.amount, args.category, args.description, expense_date)
        print(f"Added expense #{record['id']}: {record['amount']:.2f} ({record['category']}) on {record['date']}")

    elif args.command == "list":
        expenses = list_expenses(data_file, args.category, args.start_date, args.end_date)
        print_table(expenses)

    elif args.command == "update":
        try:
            record = update_expense(
                data_file, args.id,
                amount=args.amount, category=args.category,
                description=args.description, date=args.date,
            )
            print(f"Updated expense #{record['id']}.")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "delete":
        try:
            removed = delete_expense(data_file, args.id)
            print(f"Deleted expense #{removed['id']}: {removed['description']}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "summary":
        summary = summarize(data_file, args.category, args.month)
        print_summary(summary)


if __name__ == "__main__":
    main()
