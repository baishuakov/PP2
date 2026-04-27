"""
Features:
  • Filter by group
  • Search by email (partial match)
  • Sort by name / birthday / date added
  • Paginated navigation  (next / prev / quit)
  • Export contacts to JSON
  • Import contacts from JSON  (duplicate handling: skip / overwrite)
  • CSV import with extended fields (email, birthday, group, phone type)
  • Stored procedure wrappers: add_phone, move_to_group, search_contacts
"""

import csv
import json
import os
import sys
from datetime import date, datetime
from typing import Optional

import psycopg2
import psycopg2.extras

from config import PAGE_SIZE
from connect import get_connection

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause(msg: str = "\nPress Enter to continue…"):
    input(msg)


def fmt_date(d) -> str:
    """Return ISO date string or dash."""
    return d.isoformat() if d else "—"


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_contact_row(row: dict):
    """Pretty-print a single contact row (dict-like)."""
    phones = row.get("phones") or "—"
    print(
        f"  [{row['id']:>4}]  {row['name']:<25} "
        f"Email: {(row['email'] or '—'):<28} "
        f"BD: {fmt_date(row.get('birthday')):<12} "
        f"Group: {(row.get('group_name') or '—'):<10} "
        f"Phones: {phones}"
    )


# ─────────────────────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────────────────────

def get_groups(conn) -> list[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, name FROM groups ORDER BY name")
        return cur.fetchall()


def get_or_create_group(conn, group_name: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "INSERT INTO groups (name) VALUES (%s) RETURNING id", (group_name,)
        )
        gid = cur.fetchone()[0]
        conn.commit()
        return gid


def fetch_contacts_page(
    conn,
    *,
    page: int = 1,
    sort_by: str = "name",
    group_id: Optional[int] = None,
    email_filter: Optional[str] = None,
) -> tuple[list[dict], int]:
    """
    Returns (rows, total_count).
    sort_by: 'name' | 'birthday' | 'created_at'
    """
    sort_col = {"name": "c.name", "birthday": "c.birthday", "date": "c.created_at"}.get(
        sort_by, "c.name"
    )
    offset = (page - 1) * PAGE_SIZE
    conditions = []
    params: list = []

    if group_id:
        conditions.append("c.group_id = %s")
        params.append(group_id)
    if email_filter:
        conditions.append("lower(c.email) LIKE %s")
        params.append(f"%{email_filter.lower()}%")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    base_query = f"""
        SELECT c.id, c.name, c.email, c.birthday, c.created_at,
               g.name AS group_name,
               string_agg(p.phone || ' (' || p.type || ')', ', ' ORDER BY p.type) AS phones
        FROM   contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones p ON p.contact_id = c.id
        {where}
        GROUP BY c.id, c.name, c.email, c.birthday, c.created_at, g.name
        ORDER BY {sort_col} NULLS LAST
        LIMIT %s OFFSET %s
    """

    count_query = f"""
        SELECT COUNT(DISTINCT c.id)
        FROM   contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones p ON p.contact_id = c.id
        {where}
    """

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(count_query, params)
        total = cur.fetchone()["count"]

        cur.execute(base_query, params + [PAGE_SIZE, offset])
        rows = cur.fetchall()

    return rows, total


# ─────────────────────────────────────────────────────────────
# 3.2  Console Search / Filter / Sort / Paginate
# ─────────────────────────────────────────────────────────────

def browse_contacts(conn):
    """Interactive paginated browser with filter / sort options."""
    page = 1
    sort_by = "name"
    group_id = None
    email_filter = None

    while True:
        clear()
        print_header("Browse Contacts")

        rows, total = fetch_contacts_page(
            conn,
            page=page,
            sort_by=sort_by,
            group_id=group_id,
            email_filter=email_filter,
        )
        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

        print(
            f"  Page {page}/{total_pages}  |  Total: {total}  |  "
            f"Sort: {sort_by}  |  "
            f"Group filter: {group_id or 'all'}  |  "
            f"Email filter: {email_filter or 'none'}"
        )
        print("-" * 60)
        if rows:
            for row in rows:
                print_contact_row(row)
        else:
            print("  (no contacts found)")

        print("\n  n)next   p)prev   s)sort   g)group filter   e)email filter   c)clear filters   q)quit")
        cmd = input("  > ").strip().lower()

        if cmd == "n":
            if page < total_pages:
                page += 1
        elif cmd == "p":
            if page > 1:
                page -= 1
        elif cmd == "s":
            print("  Sort by: 1) name  2) birthday  3) date added")
            ch = input("  > ").strip()
            sort_by = {"1": "name", "2": "birthday", "3": "date"}.get(ch, sort_by)
            page = 1
        elif cmd == "g":
            groups = get_groups(conn)
            print("  Groups:")
            for i, g in enumerate(groups, 1):
                print(f"    {i}) {g['name']}")
            print("    0) All groups")
            ch = input("  > ").strip()
            if ch == "0":
                group_id = None
            else:
                try:
                    group_id = groups[int(ch) - 1]["id"]
                except (IndexError, ValueError):
                    pass
            page = 1
        elif cmd == "e":
            email_filter = input("  Email contains: ").strip() or None
            page = 1
        elif cmd == "c":
            group_id = None
            email_filter = None
            sort_by = "name"
            page = 1
        elif cmd == "q":
            break


# ─────────────────────────────────────────────────────────────
# 3.3  Export / Import JSON
# ─────────────────────────────────────────────────────────────

def export_json(conn):
    """Export all contacts (with phones and group) to a JSON file."""
    print_header("Export to JSON")
    path = input("  Output file path [contacts.json]: ").strip() or "contacts.json"

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT c.id, c.name, c.email,
                   c.birthday::text AS birthday,
                   c.created_at::text AS created_at,
                   g.name AS group_name
            FROM   contacts c
            LEFT JOIN groups g ON g.id = c.group_id
            ORDER BY c.name
        """)
        contacts = [dict(r) for r in cur.fetchall()]

        # Attach phones
        for contact in contacts:
            cur.execute(
                "SELECT phone, type FROM phones WHERE contact_id = %s ORDER BY type",
                (contact["id"],),
            )
            contact["phones"] = [dict(r) for r in cur.fetchall()]
            del contact["id"]  # strip internal id from export

    with open(path, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)

    print(f"\n  ✓ Exported {len(contacts)} contacts → {path}")
    pause()


def import_json(conn):
    """Import contacts from a JSON file with duplicate handling."""
    print_header("Import from JSON")
    path = input("  JSON file path [contacts.json]: ").strip() or "contacts.json"

    if not os.path.exists(path):
        print(f"  ✗ File not found: {path}")
        pause()
        return

    with open(path, encoding="utf-8") as f:
        contacts = json.load(f)

    skipped = overwritten = inserted = 0

    for c in contacts:
        name = c.get("name", "").strip()
        if not name:
            continue

        with conn.cursor() as cur:
            cur.execute("SELECT id FROM contacts WHERE name = %s LIMIT 1", (name,))
            existing = cur.fetchone()

        if existing:
            print(f"\n  Duplicate: '{name}' ")
            action = input("  (s)skip / (o)overwrite? ").strip().lower()
            if action != "o":
                skipped += 1
                continue
            # Overwrite: delete old phones, update record
            with conn.cursor() as cur:
                contact_id = existing[0]
                group_id = get_or_create_group(conn, c["group_name"]) if c.get("group_name") else None
                cur.execute(
                    "UPDATE contacts SET email=%s, birthday=%s, group_id=%s WHERE id=%s",
                    (c.get("email"), c.get("birthday"), group_id, contact_id),
                )
                cur.execute("DELETE FROM phones WHERE contact_id=%s", (contact_id,))
                for ph in c.get("phones", []):
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                        (contact_id, ph["phone"], ph.get("type", "mobile")),
                    )
            conn.commit()
            overwritten += 1
        else:
            with conn.cursor() as cur:
                group_id = get_or_create_group(conn, c["group_name"]) if c.get("group_name") else None
                cur.execute(
                    """INSERT INTO contacts (name, email, birthday, group_id)
                       VALUES (%s,%s,%s,%s) RETURNING id""",
                    (name, c.get("email"), c.get("birthday"), group_id),
                )
                contact_id = cur.fetchone()[0]
                for ph in c.get("phones", []):
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                        (contact_id, ph["phone"], ph.get("type", "mobile")),
                    )
            conn.commit()
            inserted += 1

    print(f"\n  ✓ Done — inserted: {inserted}, overwritten: {overwritten}, skipped: {skipped}")
    pause()


# ─────────────────────────────────────────────────────────────
# 3.3  CSV Import (extended fields)
# ─────────────────────────────────────────────────────────────

def import_csv(conn):
    """
    Import contacts from CSV.
    Expected columns: name, phone, phone_type, email, birthday, group
    """
    print_header("Import from CSV")
    path = input("  CSV file path [contacts.csv]: ").strip() or "contacts.csv"

    if not os.path.exists(path):
        print(f"  ✗ File not found: {path}")
        pause()
        return

    inserted = skipped = 0

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip()
            if not name:
                continue

            phone = row.get("phone", "").strip()
            phone_type = row.get("phone_type", "mobile").strip() or "mobile"
            email = row.get("email", "").strip() or None
            birthday = row.get("birthday", "").strip() or None
            group_name = row.get("group", "").strip() or None

            with conn.cursor() as cur:
                cur.execute("SELECT id FROM contacts WHERE name=%s LIMIT 1", (name,))
                existing = cur.fetchone()

            if existing:
                # Just add the phone if not already present
                contact_id = existing[0]
                if phone:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT 1 FROM phones WHERE contact_id=%s AND phone=%s",
                            (contact_id, phone),
                        )
                        if not cur.fetchone():
                            cur.execute(
                                "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                                (contact_id, phone, phone_type),
                            )
                conn.commit()
                skipped += 1
                continue

            group_id = get_or_create_group(conn, group_name) if group_name else None

            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO contacts (name, email, birthday, group_id)
                       VALUES (%s,%s,%s,%s) RETURNING id""",
                    (name, email, birthday, group_id),
                )
                contact_id = cur.fetchone()[0]
                if phone:
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                        (contact_id, phone, phone_type),
                    )
            conn.commit()
            inserted += 1

    print(f"\n  ✓ Done — inserted: {inserted}, existing (phone added if new): {skipped}")
    pause()


# ─────────────────────────────────────────────────────────────
# 3.4  Stored Procedure / Function wrappers
# ─────────────────────────────────────────────────────────────

def call_add_phone(conn):
    print_header("Add Phone Number")
    contact_name = input("  Contact name: ").strip()
    phone = input("  Phone number: ").strip()
    ptype = input("  Type (home/work/mobile): ").strip().lower()
    try:
        with conn.cursor() as cur:
            cur.execute("CALL add_phone(%s, %s, %s)", (contact_name, phone, ptype))
        conn.commit()
        print("  ✓ Phone added.")
    except Exception as e:
        conn.rollback()
        print(f"  ✗ Error: {e}")
    pause()


def call_move_to_group(conn):
    print_header("Move Contact to Group")
    contact_name = input("  Contact name: ").strip()
    group_name = input("  Group name: ").strip()
    try:
        with conn.cursor() as cur:
            cur.execute("CALL move_to_group(%s, %s)", (contact_name, group_name))
        conn.commit()
        print("  ✓ Contact moved.")
    except Exception as e:
        conn.rollback()
        print(f"  ✗ Error: {e}")
    pause()


def call_search_contacts(conn):
    print_header("Search Contacts")
    query = input("  Search query: ").strip()
    if not query:
        return
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM search_contacts(%s)", (query,))
        rows = cur.fetchall()

    if rows:
        print(f"\n  Found {len(rows)} result(s):\n")
        for row in rows:
            print_contact_row(row)
    else:
        print("  No contacts found.")
    pause()


# ─────────────────────────────────────────────────────────────
# Add contact (quick form)
# ─────────────────────────────────────────────────────────────

def add_contact(conn):
    print_header("Add New Contact")
    name = input("  Name: ").strip()
    if not name:
        return
    email = input("  Email: ").strip() or None
    birthday = input("  Birthday (YYYY-MM-DD, blank to skip): ").strip() or None
    groups = get_groups(conn)
    print("  Groups:")
    for i, g in enumerate(groups, 1):
        print(f"    {i}) {g['name']}")
    ch = input("  Select group (blank to skip): ").strip()
    group_id = None
    if ch.isdigit() and 1 <= int(ch) <= len(groups):
        group_id = groups[int(ch) - 1]["id"]

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO contacts (name, email, birthday, group_id) VALUES (%s,%s,%s,%s) RETURNING id",
            (name, email, birthday, group_id),
        )
        contact_id = cur.fetchone()[0]

    # Add phones
    while True:
        phone = input("  Phone number (blank to stop): ").strip()
        if not phone:
            break
        ptype = input("  Type (home/work/mobile): ").strip().lower() or "mobile"
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                (contact_id, phone, ptype),
            )

    conn.commit()
    print(f"  ✓ Contact '{name}' added (id={contact_id}).")
    pause()


# ─────────────────────────────────────────────────────────────
# Main menu
# ─────────────────────────────────────────────────────────────

MENU = """
  1) Browse / Filter / Sort contacts
  2) Search contacts (name / email / phone)
  3) Add new contact
  4) Add phone to existing contact
  5) Move contact to group
  ──────────────────────────────
  6) Import from CSV
  7) Import from JSON
  8) Export to JSON
  ──────────────────────────────
  0) Exit
"""


def main():
    try:
        conn = get_connection()
    except Exception as e:
        print(f"Cannot connect to database: {e}")
        sys.exit(1)

    print("  ✓ Connected to database.")

    while True:
        clear()
        print_header("Phonebook – Main Menu")
        print(MENU)
        choice = input("  > ").strip()

        if choice == "1":
            browse_contacts(conn)
        elif choice == "2":
            call_search_contacts(conn)
        elif choice == "3":
            add_contact(conn)
        elif choice == "4":
            call_add_phone(conn)
        elif choice == "5":
            call_move_to_group(conn)
        elif choice == "6":
            import_csv(conn)
        elif choice == "7":
            import_json(conn)
        elif choice == "8":
            export_json(conn)
        elif choice == "0":
            print("\n  Goodbye!\n")
            break
        else:
            print("  Unknown option.")
            pause()

    conn.close()


if __name__ == "__main__":
    main()
