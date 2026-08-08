"""
Creates a 'demo_files' folder with sample files that have messy names,
so you can immediately try out renamer.py.

Usage:
    python create_demo_files.py
    python renamer.py demo_files --find " " --replace "_" --dry-run
"""

from pathlib import Path

SAMPLE_FILES = [
    "My Vacation Photo.JPG",
    "Report Draft Final.docx",
    "IMG 2024.png",
    "budget copy.xlsx",
    "Screenshot 2026-07-29.png",
    "notes.txt",
]

def main():
    demo_dir = Path("demo_files")
    demo_dir.mkdir(exist_ok=True)

    for name in SAMPLE_FILES:
        (demo_dir / name).write_text(f"Sample content for {name}")

    print(f"Created {len(SAMPLE_FILES)} sample files in '{demo_dir}/'")
    print('Try:  python renamer.py demo_files --find " " --replace "_" --dry-run')

if __name__ == "__main__":
    main()
