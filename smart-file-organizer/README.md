# 🗂️ Smart File Organizer

**Roadmap stage:** Python Basics — Project 1
**Skills practiced:** `pathlib`, file I/O, `argparse`, `logging`, exception handling, `unittest`

A command-line tool that automatically sorts messy folders (like your
Downloads folder) into clean category sub-folders — Images, Documents,
Videos, Audio, Archives, Code, Installers, and Others — based on file
extension.

## ✨ Features

- **Dry-run mode** — preview exactly what will move before touching anything
- **Undo support** — reverse the last organize operation with one command
- **Collision-safe** — never overwrites a file; auto-renames duplicates (`file_1.txt`, `file_2.txt`, ...)
- **Logging** — every action is written to `organizer.log` inside the target folder
- **Zero dependencies** — pure Python standard library

## 📂 Project Structure

```
smart-file-organizer/
├── organizer.py           # main CLI tool
├── test_organizer.py      # unit tests (12 tests)
├── create_demo_mess.py    # generates a sample messy folder to try it on
└── README.md
```

## 🚀 Usage

### 1. Try it on a demo folder first (recommended)

```bash
python create_demo_mess.py
python organizer.py demo_mess --dry-run
```

### 2. Organize a real folder

```bash
python organizer.py "C:/Users/you/Downloads" --dry-run   # preview first!
python organizer.py "C:/Users/you/Downloads"              # actually move files
```

### 3. Undo if something looks wrong

```bash
python organizer.py "C:/Users/you/Downloads" --undo
```

## 🧪 Running Tests

```bash
python -m unittest test_organizer.py -v
```

## 🧠 What I Learned

- Working with `pathlib.Path` instead of raw string paths
- Building a real CLI with `argparse` (flags, help text, arguments)
- Designing an **undo system** using a JSON move-log — a pattern used in
  real tools like installers and migration scripts
- Writing `unittest` tests with `tempfile` so tests never touch real files
- Configuring Python's `logging` module to write to both console and file

## 🔮 Possible Future Improvements

- [ ] Add a config file (`.yaml`) so users can customize category rules
- [ ] Recursive mode to organize sub-folders too
- [ ] GUI version using `tkinter`

---
📅 Part of my [Python Basics → Production Project roadmap](../README.md).
