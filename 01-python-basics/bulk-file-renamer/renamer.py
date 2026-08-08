"""
Bulk File Renamer
------------------
A command-line tool that renames many files at once using rules you
choose: find/replace text, change case, add a prefix/suffix, or apply
sequential numbering (e.g. photo_1.jpg, photo_2.jpg, ...).

Rules are applied in this fixed order, so they can be combined:
    1. find & replace   (--find / --replace)
    2. case change       (--case upper|lower|title)
    3. prefix / suffix   (--prefix / --suffix)
    4. sequential numbering (--number, overrides the base name entirely)

Features:
- Dry-run mode: preview new names before touching anything
- Undo mode: reverse the last rename operation using a rename-log
- Extension filter: only rename files matching given extensions
- Logging: every rename is recorded to renamer.log
- Safe: never overwrites a file; skips + warns on name collisions

Usage examples:
    python renamer.py photos --prefix "trip_" --dry-run
    python renamer.py photos --find " " --replace "_"
    python renamer.py photos --case lower
    python renamer.py photos --number "vacation_{n}" --ext .jpg,.png
    python renamer.py photos --undo

Author: (your name) - Python Basics Project 2
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE_NAME = "renamer.log"
RENAME_LOG_NAME = ".renamer_last_run.json"


def setup_logging(target_dir: Path) -> None:
    log_path = target_dir / LOG_FILE_NAME
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def apply_case(name: str, mode: str) -> str:
    if mode == "upper":
        return name.upper()
    if mode == "lower":
        return name.lower()
    if mode == "title":
        return name.title()
    return name


def build_new_name(original: Path, index: int, args) -> str:
    """Compute the new filename for a single file based on CLI args."""
    stem = original.stem
    suffix = original.suffix  # includes the dot, e.g. ".jpg"

    if args.number:
        # Sequential numbering replaces the base name entirely.
        # e.g. pattern "vacation_{n}" -> "vacation_1", "vacation_2", ...
        stem = args.number.replace("{n}", str(index))
    else:
        if args.find is not None:
            stem = stem.replace(args.find, args.replace or "")
        if args.case:
            stem = apply_case(stem, args.case)
        if args.prefix:
            stem = f"{args.prefix}{stem}"
        if args.suffix:
            stem = f"{stem}{args.suffix}"

    return f"{stem}{suffix}"


def matches_extension_filter(file_path: Path, extensions) -> bool:
    if not extensions:
        return True
    return file_path.suffix.lower() in extensions


def rename(target_dir: Path, args) -> None:
    if not target_dir.exists() or not target_dir.is_dir():
        logging.error("Target folder does not exist: %s", target_dir)
        sys.exit(1)

    extensions = None
    if args.ext:
        extensions = {e.strip().lower() if e.strip().startswith(".") else f".{e.strip().lower()}"
                       for e in args.ext.split(",")}

    files = sorted(
        f for f in target_dir.iterdir()
        if f.is_file() and f.name not in (LOG_FILE_NAME, RENAME_LOG_NAME)
        and matches_extension_filter(f, extensions)
    )

    if not files:
        logging.info("No matching files found in %s", target_dir)
        return

    renames = []
    mode_label = "[DRY-RUN] " if args.dry_run else ""

    for index, file_path in enumerate(files, start=1):
        new_name = build_new_name(file_path, index, args)
        new_path = file_path.parent / new_name

        if new_name == file_path.name:
            continue  # nothing to change for this file

        if new_path.exists():
            logging.warning("Skipping %s -> %s (target already exists)",
                             file_path.name, new_name)
            continue

        logging.info("%sRename: %s  ->  %s", mode_label, file_path.name, new_name)

        if not args.dry_run:
            file_path.rename(new_path)
            renames.append({"from": str(new_path), "to": str(file_path)})

    if not args.dry_run and renames:
        rename_log_path = target_dir / RENAME_LOG_NAME
        with open(rename_log_path, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "renames": renames}, f, indent=2)
        logging.info("Renamed %d file(s). Run with --undo to reverse this.", len(renames))
    elif args.dry_run:
        logging.info("Dry-run complete. Re-run without --dry-run to apply.")


def undo(target_dir: Path) -> None:
    rename_log_path = target_dir / RENAME_LOG_NAME

    if not rename_log_path.exists():
        logging.error("No previous run found to undo in %s", target_dir)
        sys.exit(1)

    with open(rename_log_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    renames = data.get("renames", [])
    restored = 0

    for item in reversed(renames):
        current = Path(item["from"])
        original = Path(item["to"])
        if current.exists() and not original.exists():
            current.rename(original)
            logging.info("Restored: %s -> %s", current.name, original.name)
            restored += 1
        else:
            logging.warning("Could not restore %s (name conflict or already moved)", current)

    rename_log_path.unlink()
    logging.info("Undo complete. %d file(s) restored.", restored)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bulk File Renamer - rename many files at once using simple rules."
    )
    parser.add_argument("target", type=str, help="Path to the folder containing files to rename")
    parser.add_argument("--find", type=str, default=None, help="Text to find in filenames")
    parser.add_argument("--replace", type=str, default=None, help="Text to replace --find with")
    parser.add_argument("--case", choices=["upper", "lower", "title"], default=None,
                         help="Change case of the filename")
    parser.add_argument("--prefix", type=str, default=None, help="Text to add before the filename")
    parser.add_argument("--suffix", type=str, default=None, help="Text to add after the filename (before extension)")
    parser.add_argument("--number", type=str, default=None,
                         help="Sequential numbering pattern, e.g. 'photo_{n}' -> photo_1, photo_2, ...")
    parser.add_argument("--ext", type=str, default=None,
                         help="Comma-separated list of extensions to include, e.g. .jpg,.png")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without renaming any files")
    parser.add_argument("--undo", action="store_true", help="Undo the last rename operation")
    return parser.parse_args()


def main():
    args = parse_args()
    target_dir = Path(args.target).expanduser().resolve()

    setup_logging(target_dir if target_dir.exists() else Path("."))

    if args.undo:
        undo(target_dir)
    else:
        if not any([args.find is not None, args.case, args.prefix, args.suffix, args.number]):
            logging.error("No rename rule provided. Use --find/--replace, --case, "
                           "--prefix, --suffix, or --number.")
            sys.exit(1)
        rename(target_dir, args)


if __name__ == "__main__":
    main()
