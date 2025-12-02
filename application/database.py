import json
from typing import List, Dict, Any, Optional
from configfile import supabase_key, supabase_url
from PIL import Image
import requests
from io import BytesIO
import uuid
from datetime import datetime


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

        supabase.table("tokens").upsert(data).execute()

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


def save_img_to_db(BACKGROUND_PATH):
    # --- Configuration ---
    # Replace with your background image file
    OVERLAY_PATH = "cadenceoverlay.png"
    TARGET_SIZE = (1750, 1750)
    OVERLAY_MAX_WIDTH = 750
    bucket_name = "playlist"
    supabase = get_supabase_client()
    try:
        # 1. Open the images
        response = requests.get(BACKGROUND_PATH)
        background = Image.open(BytesIO(response.content)).convert("RGB")
        overlay = Image.open(OVERLAY_PATH).convert("RGBA")

        # 2. Resize the background
        background = background.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

        # 3. Resize overlay if needed
        overlay_width, overlay_height = overlay.size
        if overlay_width > OVERLAY_MAX_WIDTH:
            ratio = OVERLAY_MAX_WIDTH / overlay_width
            new_height = int(overlay_height * ratio)
            overlay = overlay.resize(
                (OVERLAY_MAX_WIDTH, new_height), Image.Resampling.LANCZOS
            )

        # 4. Calculate bottom-right position
        bg_width, bg_height = background.size
        ov_width, ov_height = overlay.size
        margin = 50
        position = (bg_width - ov_width - margin, bg_height - ov_height - margin)

        # 5. Paste overlay onto background
        background.paste(overlay, position, overlay)

        # 6. Save to BytesIO buffer instead of file
        output_buffer = BytesIO()
        background.save(
            output_buffer, format="JPEG", quality=60, optimize=True, progressive=True
        )
        output_buffer.seek(0)  # Reset buffer position to beginning

        # 7. Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_path = f"playlist/{timestamp}_{unique_id}.jpg"
        supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=output_buffer.getvalue(),
            file_options={"content-type": "image/jpeg", "cache-control": "3600"},
        )

        # 9. Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)

        print(f"Success! Image uploaded to Supabase: {public_url}")
        return public_url

    except FileNotFoundError:
        print("Error: One of the image files was not found.")
        return {"success": False, "url": None, "path": None}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"success": False, "url": None, "path": None}


def diagnose_supabase_storage(supabase_client, bucket_name="playlist"):
    """Run diagnostics on Supabase storage"""

    print("=== SUPABASE STORAGE DIAGNOSTICS ===\n")

    # 1. Check if we can connect
    print("1. Testing connection...")
    try:
        buckets = supabase_client.storage.list_buckets()
        print(f"   ✓ Connected successfully")
        print(f"   Available buckets: {[b['name'] for b in buckets]}")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return

    # 2. Check if bucket exists
    print(f"\n2. Checking if bucket '{bucket_name}' exists...")
    bucket_exists = any(b["name"] == bucket_name for b in buckets)
    if bucket_exists:
        print(f"   ✓ Bucket '{bucket_name}' exists")
        bucket_info = next(b for b in buckets if b["name"] == bucket_name)
        print(f"   Bucket info: {bucket_info}")
    else:
        print(f"   ✗ Bucket '{bucket_name}' NOT FOUND")
        return

    # 3. Try listing files
    print(f"\n3. Listing files in bucket...")
    try:
        files = supabase_client.storage.from_(bucket_name).list()
        print(f"   ✓ Can list files: {len(files)} files found")
    except Exception as e:
        print(f"   ✗ Cannot list files: {e}")

    # 4. Try a simple upload
    print(f"\n4. Testing simple upload...")
    test_data = b"Test file content"
    test_path = f"test_{uuid.uuid4().hex[:8]}.txt"

    try:
        response = supabase_client.storage.from_(bucket_name).upload(
            path=test_path, file=test_data, file_options={"content-type": "text/plain"}
        )
        print(f"   ✓ Upload successful!")
        print(f"   Response: {response}")

        # Get URL
        url = supabase_client.storage.from_(bucket_name).get_public_url(test_path)
        print(f"   Public URL: {url}")

        # Clean up test file
        try:
            supabase_client.storage.from_(bucket_name).remove([test_path])
            print(f"   ✓ Test file cleaned up")
        except:
            print(f"   (Could not delete test file)")

    except Exception as e:
        print(f"   ✗ Upload failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback

        traceback.print_exc()

    print("\n=== END DIAGNOSTICS ===\n")


# Run diagnostics
import uuid


def get_message_thread():
    """Retrieves all library entries for a specific user."""
    supabase = get_supabase_client()
    maxthread = 0
    try:
        response = supabase.table("messages").select("threadid").execute()
        # Returns a list of dictionaries
        maxid = response.data
        for id in maxid:
            if id["threadid"] > maxthread:
                maxthread = id["threadid"]

        print(maxthread)
        return maxthread
    except Exception as e:
        print(f"Error fetching library: {e}")
        return []


def is_new(user, recipient):
    supabase = get_supabase_client()
    try:
        response = supabase.rpc(
            "check_conversation_exists", {"u_id": user, "r_id": recipient}
        ).execute()

        # The raw data returned by the RPC call
        raw_data = response.data

        # Determine if a conversation exists:

        if isinstance(raw_data, bool):
            # Case 1: Supabase client returned the boolean directly
            conversation_exists = raw_data
        elif isinstance(raw_data, list) and raw_data:
            # Case 2: Supabase client returned a list (of dictionaries)
            # Safely access the value. Note: The key is the function name.
            conversation_exists = raw_data[0]["check_conversation_exists"]
        else:
            # Fallback for unexpected empty or non-existent data
            return True  # Assume it's new if data is unexpected

        # If the conversation exists (True), then it is NOT new (False)
        return not conversation_exists

    except Exception as e:
        print(f"Error calling RPC: {e}")
        # Return False, assuming a conversation might exist, or something went wrong
        return False


def get_messages(user):
    supabase = get_supabase_client()
    threads = "threadid"
    try:
        response = supabase.table("messages").select().eq("recipient", user).execute()
        # Returns a list of dictionaries
        return response.data
    except Exception as e:
        print(f"Error fetching library: {e}")
        return []
