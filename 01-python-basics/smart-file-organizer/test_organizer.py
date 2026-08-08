"""
Unit tests for organizer.py
Run with:  python -m unittest test_organizer.py -v
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from organizer import get_category, organize, undo, unique_destination


class TestGetCategory(unittest.TestCase):
    def test_image_extension(self):
        self.assertEqual(get_category(Path("photo.jpg")), "Images")

    def test_document_extension(self):
        self.assertEqual(get_category(Path("resume.pdf")), "Documents")

    def test_code_extension(self):
        self.assertEqual(get_category(Path("script.py")), "Code")

    def test_unknown_extension_goes_to_others(self):
        self.assertEqual(get_category(Path("mystery.xyz")), "Others")

    def test_case_insensitive(self):
        self.assertEqual(get_category(Path("PHOTO.JPG")), "Images")


class TestUniqueDestination(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_no_collision_returns_same_name(self):
        dest = unique_destination(self.tmp_dir, "file.txt")
        self.assertEqual(dest.name, "file.txt")

    def test_collision_appends_counter(self):
        (self.tmp_dir / "file.txt").touch()
        dest = unique_destination(self.tmp_dir, "file.txt")
        self.assertEqual(dest.name, "file_1.txt")

    def test_multiple_collisions(self):
        (self.tmp_dir / "file.txt").touch()
        (self.tmp_dir / "file_1.txt").touch()
        dest = unique_destination(self.tmp_dir, "file.txt")
        self.assertEqual(dest.name, "file_2.txt")


class TestOrganizeAndUndo(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        # Create a few sample files
        (self.tmp_dir / "photo.jpg").write_text("fake image data")
        (self.tmp_dir / "notes.txt").write_text("fake text data")
        (self.tmp_dir / "script.py").write_text("print('hello')")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_dry_run_does_not_move_files(self):
        organize(self.tmp_dir, dry_run=True)
        # Files should still be in the root, no category folders created
        self.assertTrue((self.tmp_dir / "photo.jpg").exists())
        self.assertFalse((self.tmp_dir / "Images").exists())

    def test_organize_moves_files_into_categories(self):
        organize(self.tmp_dir, dry_run=False)
        self.assertTrue((self.tmp_dir / "Images" / "photo.jpg").exists())
        self.assertTrue((self.tmp_dir / "Documents" / "notes.txt").exists())
        self.assertTrue((self.tmp_dir / "Code" / "script.py").exists())
        self.assertFalse((self.tmp_dir / "photo.jpg").exists())

    def test_move_log_created_after_organize(self):
        organize(self.tmp_dir, dry_run=False)
        move_log = self.tmp_dir / ".organizer_last_run.json"
        self.assertTrue(move_log.exists())
        data = json.loads(move_log.read_text())
        self.assertEqual(len(data["moves"]), 3)

    def test_undo_restores_original_locations(self):
        organize(self.tmp_dir, dry_run=False)
        undo(self.tmp_dir)
        self.assertTrue((self.tmp_dir / "photo.jpg").exists())
        self.assertTrue((self.tmp_dir / "notes.txt").exists())
        self.assertTrue((self.tmp_dir / "script.py").exists())
        # Category folders should now be empty (files moved back out)
        self.assertFalse((self.tmp_dir / "Images" / "photo.jpg").exists())


if __name__ == "__main__":
    unittest.main()
