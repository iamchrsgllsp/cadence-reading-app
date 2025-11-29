import json
from typing import List, Dict, Any, Optional
from configfile import supabase_key, supabase_url


# Install this package: pip install supabase
from supabase import create_client, Client

# --- Supabase Configuration (Replace with your actual details) ---
SUPABASE_URL = supabase_url
SUPABASE_KEY = supabase_key  # Use your public anon key for read operations
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


def get_top_five_by_username(username: str) -> list:
    supabase = get_supabase_client()
    response = (
        supabase.table("topfive")
        .select("items")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    # Returns the value of 'items' from the first dictionary found,
    # or an empty list if no data or no 'items' key is present.
    if response.data:
        return response.data[0].get("items", [])

    return []


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
        response = supabase.table("topfive").upsert(data_to_insert).execute()

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
            "status": "",  # Assuming initial status is 'To Be Read'
        }

        response = supabase.table("library").insert(data_to_insert).execute()

        print(f"Book added to library for {user}. Status: {response.status_code}")
    except Exception as e:
        print(f"Error adding book to library: {e}")


def add_full_token_info(user: str, token_info: dict):
    """
    Stores complete token information including refresh token and expiry.
    This allows token refresh without re-authentication.
    """
    supabase = get_supabase_client()
    try:
        data = {
            "username": user,
            "access_token": token_info.get("access_token"),
            "refresh_token": token_info.get("refresh_token"),
            "expires_at": token_info.get("expires_at"),
            "token_type": token_info.get("token_type", "Bearer"),
            "scope": token_info.get("scope"),
        }

        response = supabase.table("tokens").upsert(data).execute()

        print(f"Full token info stored for {user}")

    except Exception as e:
        print(f"Error storing token info: {e}")


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


def save_img_to_db(file_path, output_buffer):
    """
    Creates a composite image and uploads it to Supabase storage.

    Args:
        BACKGROUND_PATH: URL or path to background image
        supabase_client: Initialized Supabase client
        bucket_name: Name of the Supabase storage bucket

    Returns:
        dict: {'success': bool, 'url': str or None, 'path': str or None}
    """

    # --- Configuration ---
    supabase = get_supabase_client()

    # 8. Upload to Supabase
    supabase.storage.from_("playlist").upload(
        path=file_path,
        file=output_buffer.getvalue(),
        file_options={"content-type": "image/jpeg", "cache-control": "3600"},
    )

    # 9. Get public URL
    public_url = supabase.storage.from_("playlist").get_public_url(file_path)

    print(f"Success! Image uploaded to Supabase: {public_url}")
    return public_url
