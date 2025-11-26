import json
from typing import List, Dict, Any, Optional

# Install this package: pip install supabase
from supabase import create_client, Client

# --- Supabase Configuration (Replace with your actual details) ---
SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"  # Use your public anon key for read operations
# For write/update operations, consider using a Service Role key securely
# in a production environment, or handle authentication/Row Level Security (RLS)
# for user-facing applications.
# -----------------------------------------------------------------


def get_supabase_client() -> Client:
    """Initializes and returns the Supabase client."""
    # Ensure URL and Key are set before running
    if SUPABASE_URL == "YOUR_SUPABASE_URL" or SUPABASE_KEY == "YOUR_SUPABASE_ANON_KEY":
        raise ValueError(
            "Please set SUPABASE_URL and SUPABASE_KEY with your actual credentials."
        )

    return create_client(SUPABASE_URL, SUPABASE_KEY)


# --- Table Schemas (PostgreSQL/Supabase) ---
# topfive:
# id (serial/primary key)
# username (text/not null)
# items (jsonb/default '[]') - PostgreSQL has native JSON support (jsonb)

# library:
# id (serial/primary key)
# username (text/not null)
# book (jsonb/default '[]')
# status (text)
# pages_read (integer)
# total_pages (integer)
# version (text)
# ---------------------------------------------

## 📚 Top Five Functions


def get_top_five_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Retrieves the top five list for a specific username."""
    supabase = get_supabase_client()
    try:
        response = (
            supabase.table("topfive")
            .select("*")
            .eq("username", username)
            .limit(1)
            .execute()
        )

        # The result is a dict with a 'data' key which is a list
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching top five: {e}")
        return None


def amend_top_five(username: str, items: List[Any]):
    """
    Inserts or updates the top five list for a user.
    Note: Supabase recommends using `upsert` for "insert or update" logic,
    but here we'll check if the user exists and either insert or update.
    For simplicity in matching the original's *insert* behavior, this version
    performs an insert. For *upsert* logic, you'd use `.upsert()`.
    """
    supabase = get_supabase_client()
    try:
        # PostgreSQL/Supabase can handle JSON directly, so we pass the list
        data_to_insert = {
            "username": username,
            # In Supabase/Postgres, you can pass the Python list/dict directly
            # if the column type is JSONB/JSON.
            "items": items,
        }

        # Using insert. If you need to update existing, use .upsert() or .update().
        # Since the original was an INSERT, we keep it as a simple insert.
        response = supabase.table("topfive").insert(data_to_insert).execute()

        print(
            f"Top five list inserted/updated for {username}. Status: {response.status_code}"
        )
    except Exception as e:
        print(f"Error amending top five: {e}")


## 📖 Library Functions


def get_library(user: str) -> List[Dict[str, Any]]:
    """Retrieves all library entries for a specific user."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("library").select("*").eq("username", user).execute()
        # Returns a list of dictionaries
        return response.data
    except Exception as e:
        print(f"Error fetching library: {e}")
        return []


def add_book_to_library(user: str, book: List[Any], pages: int):
    """Adds a new book entry to the library."""
    supabase = get_supabase_client()
    try:
        # Check if book already exists for user (optional enhancement)
        # This check isn't in the original SQLite, but is good practice:
        # response_check = supabase.table("library").select("*").eq("username", user).eq("book", book).execute()
        # if response_check.data: print("Book already exists!")

        data_to_insert = {
            "username": user,
            "book": book,
            "total_pages": pages,
            "status": "tbr",  # Assuming initial status is 'To Be Read'
        }

        response = supabase.table("library").insert(data_to_insert).execute()

        print(f"Book added to library for {user}. Status: {response.status_code}")
    except Exception as e:
        print(f"Error adding book to library: {e}")


def remove_from_library(user: str, book_id: int):
    """Removes a book from the library by its ID."""
    supabase = get_supabase_client()
    try:
        response = (
            supabase.table("library")
            .delete()
            .eq("username", user)
            .eq("id", book_id)
            .execute()
        )

        print(
            f"Book ID {book_id} removed from library for {user}. Status: {response.status_code}"
        )
    except Exception as e:
        print(f"Error removing book: {e}")


def update_book_progress(user: str, book_id: int, pages_read: int):
    """Updates the pages read for a specific book."""
    supabase = get_supabase_client()
    try:
        response = (
            supabase.table("library")
            .update({"pages_read": pages_read})
            .eq("username", user)
            .eq("id", book_id)
            .execute()
        )

        print(f"Progress updated for book ID {book_id}. Status: {response.status_code}")
    except Exception as e:
        print(f"Error updating book progress: {e}")


def update_book_status(user: str, book_id: int, status: str):
    """Generic function to update the status of a book."""
    supabase = get_supabase_client()
    try:
        response = (
            supabase.table("library")
            .update({"status": status})
            .eq("username", user)
            .eq("id", book_id)
            .execute()
        )

        print(
            f"Status updated to '{status}' for book ID {book_id}. Status: {response.status_code}"
        )
    except Exception as e:
        print(f"Error updating book status: {e}")


# Rewritten functions using the generic update_book_status
def update_currentbook(user: str, book_id: int):
    """Sets a book's status to 'reading'."""
    update_book_status(user, book_id, "reading")


def dnfbook(user: str, book_id: int):
    """Sets a book's status to 'dnf' (Did Not Finish)."""
    update_book_status(user, book_id, "dnf")


def complete_currentbook(user: str, book_id: int):
    """Sets a book's status to 'completed'."""
    update_book_status(user, book_id, "completed")
