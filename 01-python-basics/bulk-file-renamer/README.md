# 🏷️ Bulk File Renamer

**Roadmap stage:** Python Basics — Project 2
**Skills practiced:** string manipulation, `pathlib`, `argparse`, `logging`, JSON, `unittest`

A command-line tool that renames many files at once — find & replace text,
change case, add a prefix/suffix, or apply sequential numbering (e.g.
`vacation_1.jpg`, `vacation_2.jpg`, ...). Rules can be combined in a single
run.

## ✨ Features

- **Multiple rename rules**, applied in a fixed, predictable order:
  1. find & replace text in the filename
  2. change case (`upper` / `lower` / `title`)
  3. add prefix / suffix
  4. sequential numbering (overrides the base name entirely)
- **Dry-run mode** — preview every new name before anything is renamed
- **Undo support** — reverse the last rename operation with one command
- **Extension filter** — only rename files matching given extensions (`--ext .jpg,.png`)
- **Collision-safe** — skips (and warns) instead of overwriting existing files
- **Logging** — every rename is written to `renamer.log`
- **Zero dependencies** — pure Python standard library

## 📂 Project Structure

```
bulk-file-renamer/
├── renamer.py             # main CLI tool
├── test_renamer.py        # unit tests (14 tests)
├── create_demo_files.py   # generates sample messy-named files to try it on
└── README.md
```

## 🚀 Usage

### 1. Try it on demo files first (recommended)

```bash
python create_demo_files.py
python renamer.py demo_files --find " " --replace "_" --case lower --dry-run
```

### 2. Common real-world examples

```bash
# Replace spaces with underscores and lowercase everything
python renamer.py "C:/Users/you/Downloads" --find " " --replace "_" --case lower

# Add a prefix to every file
python renamer.py my_photos --prefix "trip2026_"

# Sequentially number only images
python renamer.py my_photos --number "vacation_{n}" --ext .jpg,.png

# Always preview first!
python renamer.py my_photos --number "vacation_{n}" --dry-run
```

### 3. Undo if something looks wrong

```bash
python renamer.py my_photos --undo
```

## 🧪 Running Tests

```bash
python -m unittest test_renamer.py -v
```

## 🧠 What I Learned

- String manipulation patterns (`.replace()`, `.upper()`, `.lower()`, `.title()`)
- Designing a CLI where **multiple optional flags combine predictably**
  (deciding and documenting the order rules are applied in)
- Reusing the **dry-run + JSON undo-log pattern** from Project 1 in a new
  context — a sign this is becoming a repeatable design pattern, not a
  one-off trick
- Handling edge cases: name collisions, files with no change needed,
  filtering by extension

## 🔮 Possible Future Improvements

- [ ] Regex-based find & replace (`--regex`) for advanced patterns
- [ ] Rename based on file metadata (e.g. photo date taken, EXIF data)
- [ ] Recursive mode for renaming inside sub-folders

---
📅 Part of my [Python Basics → Production Project roadmap](../README.md).
