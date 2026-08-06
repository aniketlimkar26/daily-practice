"""
Seeds expenses.json with sample data so you can immediately try out
list/update/delete/summary without typing a bunch of 'add' commands.

Usage:
    python seed_demo_data.py
    python tracker.py list
    python tracker.py summary
"""

from pathlib import Path
from tracker import add_expense

SAMPLE_EXPENSES = [
    (12.50, "Food", "Lunch", "2026-07-01"),
    (45.00, "Transport", "Bus pass", "2026-07-05"),
    (8.75, "Food", "Coffee", "2026-07-10"),
    (120.00, "Utilities", "Electricity bill", "2026-07-12"),
    (35.20, "Entertainment", "Movie night", "2026-07-15"),
    (60.00, "Food", "Groceries", "2026-07-18"),
    (15.00, "Transport", "Taxi", "2026-08-02"),
]

def main():
    data_file = Path("expenses.json")
    if data_file.exists():
        print("expenses.json already exists. Delete it first if you want a fresh seed.")
        return

    for amount, category, description, expense_date in SAMPLE_EXPENSES:
        add_expense(data_file, amount, category, description, expense_date)

    print(f"Seeded {len(SAMPLE_EXPENSES)} sample expenses into expenses.json")
    print("Try:  python tracker.py list")
    print("      python tracker.py summary")

if __name__ == "__main__":
    main()
