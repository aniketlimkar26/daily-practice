"""
Unit tests for renamer.py
Run with:  python -m unittest test_renamer.py -v
"""

import argparse
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from renamer import build_new_name, matches_extension_filter, rename, undo


def make_args(**overrides):
    """Helper to build an argparse.Namespace with sensible defaults."""
    defaults = dict(
        find=None, replace=None, case=None, prefix=None,
        suffix=None, number=None, ext=None, dry_run=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class TestBuildNewName(unittest.TestCase):
    def test_prefix(self):
        args = make_args(prefix="trip_")
        self.assertEqual(build_new_name(Path("photo.jpg"), 1, args), "trip_photo.jpg")

    def test_suffix(self):
        args = make_args(suffix="_final")
        self.assertEqual(build_new_name(Path("report.docx"), 1, args), "report_final.docx")

    def test_find_replace(self):
        args = make_args(find=" ", replace="_")
        self.assertEqual(build_new_name(Path("my photo.jpg"), 1, args), "my_photo.jpg")

    def test_case_lower(self):
        args = make_args(case="lower")
        self.assertEqual(build_new_name(Path("IMG_FILE.JPG"), 1, args), "img_file.JPG")

    def test_sequential_numbering(self):
        args = make_args(number="vacation_{n}")
        self.assertEqual(build_new_name(Path("whatever.png"), 3, args), "vacation_3.png")

    def test_combined_find_case_prefix(self):
        args = make_args(find=" ", replace="_", case="lower", prefix="img_")
        self.assertEqual(build_new_name(Path("My Photo.JPG"), 1, args), "img_my_photo.JPG")


class TestExtensionFilter(unittest.TestCase):
    def test_matches_when_extension_in_set(self):
        self.assertTrue(matches_extension_filter(Path("a.jpg"), {".jpg", ".png"}))

    def test_does_not_match_other_extension(self):
        self.assertFalse(matches_extension_filter(Path("a.txt"), {".jpg", ".png"}))

    def test_no_filter_matches_everything(self):
        self.assertTrue(matches_extension_filter(Path("a.anything"), None))


class TestRenameAndUndo(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        (self.tmp_dir / "my photo.jpg").write_text("data")
        (self.tmp_dir / "my report.docx").write_text("data")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_dry_run_does_not_rename(self):
        args = make_args(prefix="new_", dry_run=True)
        rename(self.tmp_dir, args)
        self.assertTrue((self.tmp_dir / "my photo.jpg").exists())

    def test_rename_applies_prefix(self):
        args = make_args(prefix="new_", dry_run=False)
        rename(self.tmp_dir, args)
        self.assertTrue((self.tmp_dir / "new_my photo.jpg").exists())
        self.assertTrue((self.tmp_dir / "new_my report.docx").exists())

    def test_rename_log_created(self):
        args = make_args(prefix="new_", dry_run=False)
        rename(self.tmp_dir, args)
        log_path = self.tmp_dir / ".renamer_last_run.json"
        self.assertTrue(log_path.exists())
        data = json.loads(log_path.read_text())
        self.assertEqual(len(data["renames"]), 2)

    def test_undo_restores_original_names(self):
        args = make_args(prefix="new_", dry_run=False)
        rename(self.tmp_dir, args)
        undo(self.tmp_dir)
        self.assertTrue((self.tmp_dir / "my photo.jpg").exists())
        self.assertTrue((self.tmp_dir / "my report.docx").exists())
        self.assertFalse((self.tmp_dir / "new_my photo.jpg").exists())

    def test_extension_filter_skips_non_matching_files(self):
        args = make_args(prefix="new_", ext=".jpg", dry_run=False)
        rename(self.tmp_dir, args)
        self.assertTrue((self.tmp_dir / "new_my photo.jpg").exists())
        # .docx file should be untouched
        self.assertTrue((self.tmp_dir / "my report.docx").exists())


if __name__ == "__main__":
    unittest.main()
