import time
import urllib.parse
import requests
import re

from application.gr_importer import get_supabase_admin_client


def clean_query(text):
    if not text:
        return ""
    # Strip out anything inside parentheses (like subtitle info: "(The Bloodsworn Saga, #2)")
    text = re.sub(r"\(.*\)", "", text)
    # Remove special characters, leaving only alphanumeric and spaces
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def background_upload_task(app_to_context, data, user, bookkey):
    """
    Runs completely separate from the HTTP request cycle.
    Allows Flask to respond to the user while this processes Google Books queries.
    """
    # CRITICAL: Re-create the Flask app context so DB queries work inside the thread
    print(data)
    with app_to_context.app_context():
        print(f"--- Starting background process for {len(data)} books ---")
        print(f"User: {user}")
        failed_uploads = []
        successful_uploads = []
        for book in data:
            clean_title = clean_query(book.get("Title", ""))
            clean_author = clean_query(book.get("Author", ""))

            safe_title = urllib.parse.quote(clean_title)
            safe_author = urllib.parse.quote(clean_author)
            print(f"Querying Google Books API for: {clean_title} by {clean_author}")
            # 1. URL encode the queries to handle spaces and special characters safely

            url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{safe_title}+inauthor:{safe_author}&key={bookkey}"

            try:
                response = requests.get(url)
                response.raise_for_status()  # Check for HTTP errors

                # 2. Changed variable name to api_response to avoid overwriting 'data'
                api_response = response.json()
            except requests.RequestException as e:
                print(f"API request failed for {safe_title} by {safe_author}: {e}")
                failed_uploads.append(book)
                continue

            items = api_response.get("items", [])

            # 3. Check if any books were actually found
            if not items:
                print(f"No results found for: {safe_title} by {safe_author}")
                failed_uploads.append(book)
                continue

            # Get the first match
            first_match = items[0]

            # 4. Extract data from the nested 'volumeInfo' object
            volume_info = first_match.get("volumeInfo", {})

            title = volume_info.get("title", "Unknown Title")

            # 5. Handle authors list safely
            authors_list = volume_info.get("authors", [])
            author = ", ".join(authors_list) if authors_list else "Unknown Author"

            # 6. Safely grab thumbnail, isbn, pages, and description
            cover_url = volume_info.get("imageLinks", {}).get("thumbnail", "")

            # Look for ISBN_13 if available, otherwise fallback to any identifier
            identifiers = volume_info.get("industryIdentifiers", [])
            isbn = "No ISBN"
            for identifier in identifiers:
                if identifier.get("type") in ["ISBN_13", "ISBN_10"]:
                    isbn = identifier.get("identifier")
                    break

            pages = str(volume_info.get("pageCount", 0))
            description = volume_info.get("description", "No description available.")
            successful_uploads.append(
                {
                    "user_id": user,
                    "title": title,
                    "author": author,
                    "isbn": isbn,
                    "cover_url": cover_url,
                    "total_pages": pages,
                    "description": description,
                }
            )
        print(f"Successfully uploaded {len(successful_uploads)} books for user {user}.")
        print(f"Failed to upload {len(failed_uploads)} books for user {user}.")
        supabase = get_supabase_admin_client()

        response = supabase.table("library").upsert(successful_uploads).execute()
        print(f"Supabase insert response: {response}")
