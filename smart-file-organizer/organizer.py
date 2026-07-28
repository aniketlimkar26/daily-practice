"""
Smart File Organizer
---------------------
A command-line tool that scans a target folder and automatically sorts
files into category sub-folders (Images, Documents, Videos, Audio,
Archives, Code, Others) based on their file extension.

Features:
- Dry-run mode: preview what WOULD happen without moving anything
- Undo mode: reverse the last organize operation using a move-log
- Logging: every action is recorded to organizer.log
- Safe: never overwrites a file; auto-renames on name collisions

Usage:
    python organizer.py <target_folder>                 # organize
    python organizer.py <target_folder> --dry-run        # preview only
    python organizer.py <target_folder> --undo           # undo last run

Author: (your name) - Python Basics Project 1
"""

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------
# Configuration: map file extensions -> category folder name
# --------------------------------------------------------------------------
CATEGORY_MAP = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".xls", ".ppt",
                  ".pptx", ".csv", ".md"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".m4a"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".json",
             ".sql", ".sh"],
    "Installers": [".exe", ".msi", ".apk", ".dmg"],
}

LOG_FILE_NAME = "organizer.log"
MOVE_LOG_NAME = ".organizer_last_run.json"  # used for undo


def setup_logging(target_dir: Path) -> None:
    """Configure logging to both console and a log file inside the target dir."""
    log_path = target_dir / LOG_FILE_NAME
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def get_category(file_path: Path) -> str:
    """Return the category folder name for a given file, based on extension."""
    ext = file_path.suffix.lower()
    for category, extensions in CATEGORY_MAP.items():
        if ext in extensions:
            return category
    return "Others"


def unique_destination(dest_folder: Path, file_name: str) -> Path:
    """
    Return a destination path that does not already exist.
    If 'photo.jpg' exists, tries 'photo_1.jpg', 'photo_2.jpg', etc.
    """
    dest = dest_folder / file_name
    if not dest.exists():
        return dest

    stem = Path(file_name).stem
    suffix = Path(file_name).suffix
    counter = 1
    while True:
        candidate = dest_folder / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def organize(target_dir: Path, dry_run: bool = False) -> None:
    """Scan target_dir (non-recursively) and sort files into category folders."""
    if not target_dir.exists() or not target_dir.is_dir():
        logging.error("Target folder does not exist: %s", target_dir)
        sys.exit(1)

    files = [f for f in target_dir.iterdir() if f.is_file()
             and f.name not in (LOG_FILE_NAME, MOVE_LOG_NAME)]

    if not files:
        logging.info("No files to organize in %s", target_dir)
        return

    moves = []  # record of (original_path, new_path) for undo support
    mode_label = "[DRY-RUN] " if dry_run else ""

    for file_path in files:
        category = get_category(file_path)
        dest_folder = target_dir / category
        dest_path = unique_destination(dest_folder, file_path.name)

        logging.info("%sMove: %s  ->  %s/%s",
                      mode_label, file_path.name, category, dest_path.name)

        if not dry_run:
            dest_folder.mkdir(exist_ok=True)
            shutil.move(str(file_path), str(dest_path))
            moves.append({"from": str(dest_path), "to": str(file_path)})

    if not dry_run and moves:
        move_log_path = target_dir / MOVE_LOG_NAME
        with open(move_log_path, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "moves": moves}, f, indent=2)
        logging.info("Organized %d file(s). Run with --undo to reverse this.", len(moves))
    elif dry_run:
        logging.info("Dry-run complete. %d file(s) would be moved. "
                      "Re-run without --dry-run to apply.", len(files))


def undo(target_dir: Path) -> None:
    """Reverse the most recent organize operation using the saved move-log."""
    move_log_path = target_dir / MOVE_LOG_NAME

    if not move_log_path.exists():
        logging.error("No previous run found to undo in %s", target_dir)
        sys.exit(1)

    with open(move_log_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    moves = data.get("moves", [])
    restored = 0

    for move in reversed(moves):
        src = Path(move["from"])
        dest = Path(move["to"])
        if src.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            logging.info("Restored: %s -> %s", src.name, dest)
            restored += 1
        else:
            logging.warning("Could not find %s to restore (already moved?)", src)

    move_log_path.unlink()
    logging.info("Undo complete. %d file(s) restored.", restored)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Smart File Organizer - sort files into category folders."
    )
    parser.add_argument("target", type=str, help="Path to the folder to organize")
    parser.add_argument("--dry-run", action="store_true",
                         help="Preview changes without moving any files")
    parser.add_argument("--undo", action="store_true",
                         help="Undo the last organize operation")
    return parser.parse_args()


def main():
    args = parse_args()
    target_dir = Path(args.target).expanduser().resolve()

    setup_logging(target_dir if target_dir.exists() else Path("."))

    if args.undo:
        undo(target_dir)
    else:
        organize(target_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
