"""
Unit tests for tracker.py
Run with:  python -m unittest test_tracker.py -v
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from tracker import (
    add_expense, delete_expense, list_expenses,
    next_id, summarize, update_expense, validate_date,
)


class TestValidateDate(unittest.TestCase):
    def test_valid_date_passes(self):
        self.assertEqual(validate_date("2026-07-29"), "2026-07-29")

    def test_invalid_date_raises(self):
        with self.assertRaises(ValueError):
            validate_date("29-07-2026")


class TestNextId(unittest.TestCase):
    def test_empty_list_returns_1(self):
        self.assertEqual(next_id([]), 1)

    def test_increments_from_max(self):
        expenses = [{"id": 1}, {"id": 5}, {"id": 3}]
        self.assertEqual(next_id(expenses), 6)


class TestCRUD(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.data_file = self.tmp_dir / "expenses.json"

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_add_expense_creates_record(self):
        record = add_expense(self.data_file, 12.5, "Food", "Lunch", "2026-07-29")
        self.assertEqual(record["id"], 1)
        self.assertEqual(record["amount"], 12.5)
        self.assertEqual(record["category"], "Food")

    def test_add_multiple_expenses_increments_id(self):
        add_expense(self.data_file, 10, "Food", "Snack", "2026-07-01")
        second = add_expense(self.data_file, 20, "Transport", "Bus", "2026-07-02")
        self.assertEqual(second["id"], 2)

    def test_list_expenses_returns_all_sorted_by_date(self):
        add_expense(self.data_file, 10, "Food", "B", "2026-07-05")
        add_expense(self.data_file, 20, "Food", "A", "2026-07-01")
        result = list_expenses(self.data_file)
        self.assertEqual([e["description"] for e in result], ["A", "B"])

    def test_list_filters_by_category(self):
        add_expense(self.data_file, 10, "Food", "Lunch", "2026-07-01")
        add_expense(self.data_file, 20, "Transport", "Bus", "2026-07-01")
        result = list_expenses(self.data_file, category="food")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["category"], "Food")

    def test_list_filters_by_date_range(self):
        add_expense(self.data_file, 10, "Food", "A", "2026-07-01")
        add_expense(self.data_file, 20, "Food", "B", "2026-07-15")
        add_expense(self.data_file, 30, "Food", "C", "2026-07-31")
        result = list_expenses(self.data_file, start_date="2026-07-10", end_date="2026-07-20")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["description"], "B")

    def test_update_expense_changes_fields(self):
        add_expense(self.data_file, 10, "Food", "Lunch", "2026-07-01")
        updated = update_expense(self.data_file, 1, amount=15.0, description="Lunch + coffee",
                                  category=None, date=None)
        self.assertEqual(updated["amount"], 15.0)
        self.assertEqual(updated["description"], "Lunch + coffee")
        self.assertEqual(updated["category"], "Food")  # unchanged

    def test_update_nonexistent_id_raises(self):
        with self.assertRaises(ValueError):
            update_expense(self.data_file, 999, amount=1.0, category=None,
                            description=None, date=None)

    def test_delete_expense_removes_record(self):
        add_expense(self.data_file, 10, "Food", "Lunch", "2026-07-01")
        removed = delete_expense(self.data_file, 1)
        self.assertEqual(removed["description"], "Lunch")
        self.assertEqual(list_expenses(self.data_file), [])

    def test_delete_nonexistent_id_raises(self):
        with self.assertRaises(ValueError):
            delete_expense(self.data_file, 999)


class TestSummarize(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.data_file = self.tmp_dir / "expenses.json"
        add_expense(self.data_file, 10, "Food", "Lunch", "2026-07-01")
        add_expense(self.data_file, 20, "Food", "Dinner", "2026-07-02")
        add_expense(self.data_file, 30, "Transport", "Bus", "2026-08-01")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_total_and_count(self):
        summary = summarize(self.data_file)
        self.assertEqual(summary["total"], 60)
        self.assertEqual(summary["count"], 3)

    def test_by_category_breakdown(self):
        summary = summarize(self.data_file)
        self.assertEqual(summary["by_category"]["Food"], 30)
        self.assertEqual(summary["by_category"]["Transport"], 30)

    def test_filter_by_month(self):
        summary = summarize(self.data_file, month="2026-07")
        self.assertEqual(summary["total"], 30)
        self.assertEqual(summary["count"], 2)

    def test_filter_by_category(self):
        summary = summarize(self.data_file, category="Food")
        self.assertEqual(summary["total"], 30)
        self.assertEqual(summary["count"], 2)


if __name__ == "__main__":
    unittest.main()
