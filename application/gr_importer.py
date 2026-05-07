import csv
from datetime import datetime
import json
import io
import uuid

from flask import jsonify
from configfile import supabase_url, supabase_service
from supabase import create_client, Client

SUPABASE_URL = supabase_url
SUPABASE_KEY = supabase_service


def get_supabase_admin_client() -> Client:
    """Initializes and returns the Supabase client."""
    # Ensure URL and Key are set before running
    if SUPABASE_URL == "YOUR_SUPABASE_URL" or SUPABASE_KEY == "YOUR_SUPABASE_ANON_KEY":
        raise ValueError(
            "Please set SUPABASE_URL and SUPABASE_KEY with your actual credentials."
        )

    return create_client(SUPABASE_URL, SUPABASE_KEY)


from application.database import send_message


def clean_isbn(val):
    # Removes =" and " from the string, then strips whitespace
    return val.replace('="', "").replace('"', "").strip()


def gr_import_parser(file_content, user=None, token=None):
    json_file_path = "data.json"
    data = []

    # Use io.StringIO to treat the string like a file
    # This avoids having to save the file to the hard drive
    stream = io.StringIO(file_content)
    csv_reader = csv.DictReader(stream)

    for row in csv_reader:
        data.append(row)

    # Write to JSON (optional, if you need a physical copy)
    with open(json_file_path, "w", encoding="utf-8") as jsonf:
        json.dump(data, jsonf, indent=4)

    books = []
    not_found_count = []
    for entry in data:
        isbn13 = clean_isbn(entry.get("ISBN13", ""))
        isbn = clean_isbn(entry.get("ISBN", ""))

        if isbn13 or isbn:
            # Update the entry with cleaned values if you want to use them later
            entry["ISBN13"] = isbn13
            entry["ISBN"] = isbn
            books.append(entry)
        else:
            not_found_count.append(entry)

    process_imported_data(books, user, token)  # Process the valid entries as needed
    notify_user(user, not_found_count)  # Notify the user about entries without ISBNs
    print(
        f"User {user} has {len(books)} valid entries and {len(not_found_count)} entries without ISBNs."
    )

    not_found_json = {}
    for idx, entry in enumerate(not_found_count):
        not_found_json[str(idx)] = entry
    # Return the data so your route can use it
    return not_found_json


def process_imported_data(data, user, token):
    if not data or not isinstance(data, list):
        raise ValueError("data must be a non-empty list")
    if not all(isinstance(entry, dict) for entry in data):
        raise ValueError("Each entry in data must be a dict")

    # Build the JSONB payload — keyed by index to preserve order
    import_payload = {str(idx): entry for idx, entry in enumerate(data)}

    row = {
        "user_id": user,
        "import_details": import_payload,
        "created_at": datetime.utcnow().isoformat(),
    }
    print(user)
    print(type(user))
    supabase = get_supabase_admin_client()

    response = supabase.table("import_details").insert(row).execute()

    if not response.data:
        raise Exception(f"Supabase insert failed: {response}")

    inserted_row = response.data[0]
    print(
        f"[import] Inserted row id={inserted_row['id']} for user={user} ({len(data)} records)"
    )

    return inserted_row


def notify_user(user, data):
    # This function can be used to send a notification to the user after processing the import
    # For example, you could send an email, an in-app notification, etc.
    # For now, it just prints a message to the console.
    print(f"User {user} has imported {len(data)} records.")
