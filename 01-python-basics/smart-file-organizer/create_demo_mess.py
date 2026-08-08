"""
Creates a 'demo_mess' folder full of empty sample files with varied
extensions, so you can immediately try out organizer.py without hunting
for real files to test on.

Usage:
    python create_demo_mess.py
    python organizer.py demo_mess --dry-run
    python organizer.py demo_mess
"""

from pathlib import Path

SAMPLE_FILES = [
    "vacation_photo.jpg", "screenshot.png", "diagram.svg",
    "resume.pdf", "notes.txt", "budget.xlsx", "readme.md",
    "movie_clip.mp4", "song.mp3",
    "project_backup.zip",
    "app.py", "index.html", "styles.css", "data.json",
    "setup.exe",
    "unknown_file.xyz123",
]

def main():
    demo_dir = Path("demo_mess")
    demo_dir.mkdir(exist_ok=True)

    for name in SAMPLE_FILES:
        (demo_dir / name).write_text(f"Sample content for {name}")

    print(f"Created {len(SAMPLE_FILES)} sample files in '{demo_dir}/'")
    print("Try:  python organizer.py demo_mess --dry-run")

if __name__ == "__main__":
    main()
