"""
Creates a sample contacts.csv so you can immediately try the 'bulk'
command without setting up your own recipient list first.

Usage:
    python create_sample_contacts.py
    python automation.py bulk --csv contacts.csv --subject "Hi {name}!" \\
        --body "Hello {name}, welcome to {company}." --dry-run
"""

import csv

SAMPLE_CONTACTS = [
    {"email": "alice@example.com", "name": "Alice", "company": "Acme Corp"},
    {"email": "bob@example.com", "name": "Bob", "company": "Widgets Inc"},
    {"email": "carol@example.com", "name": "Carol", "company": "Globex"},
]


def main():
    with open("contacts.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "name", "company"])
        writer.writeheader()
        writer.writerows(SAMPLE_CONTACTS)

    print(f"Created contacts.csv with {len(SAMPLE_CONTACTS)} sample contacts")
    print('Try:  python automation.py bulk --csv contacts.csv --subject "Hi {name}!" '
          '--body "Hello {name}, welcome to {company}." --dry-run')


if __name__ == "__main__":
    main()
