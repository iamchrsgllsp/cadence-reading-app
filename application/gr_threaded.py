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
    with app_to_context.app_context():
        supabase = get_supabase_admin_client()
        def sanitize(text):
            if not text: return ""
            # Remove characters that break PostgREST logic
            return re.sub(r"[(),']", "", str(text))
        title_map = {sanitize(b.get("Title")): b.get("Title") for b in data if b.get("Title")}
        target_titles = list(title_map.keys())
              
        
        # 1. Define the columns you want (everything except id and created_at)
        # Replace these with the actual column names in your 'cache_library' table
        columns = "title, authors, isbn, cover_url, pages, description"
        
        # 2. Select only the desired columns
        response = supabase.table("cached_library") \
            .select(columns) \
            .or_(f"title.in.({','.join(target_titles)})") \
            .execute()
        
        # 3. Build the map using the filtered data
        cache_map = {}
        for item in response.data:
            if item.get('title'): cache_map[item['title']] = item
            
        successful_uploads = []
        failed_uploads = []    
        successful_cache = []
        failed_cache = []
        
        for book in data:
            title = book.get("Title")     
            cached_data = cache_map.get(title)
            
            if cached_data:
                print(cached_data)
                successful_cache.append(cached_data)
            else:
                failed_cache.append(book)

        if successful_cache:
            # 1. Prepare the data for the new table
            # We add 'user_id' to each dict and rename/filter keys if necessary
            library_entries = []
            
            for item in successful_cache:
                # Create a new dictionary to match your 'library' table schema
                entry = {
                    "user_id": user,              # Inject the current user
                    "title": item.get("title"),
                    "author": item.get("authors"),
                    "isbn": item.get("isbn"),
                    "cover_url": item.get("cover_url"),
                    "total_pages": item.get("pages"),
                    "description": item.get("description")
                }
                library_entries.append(entry)

            # 2. Bulk insert into the library table
            try:
                supabase.table("library").upsert(library_entries).execute()
                print(f"Successfully moved {len(library_entries)} items from cache to library.")
            except Exception as e:
                print(f"Error inserting into library: {e}")

        for book in failed_cache:
            clean_title = clean_query(book.get("title", ""))
            clean_author = clean_query(book.get("authors", ""))

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

            pages = str(volume_info.get("pageCount"))
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
        # 1. After successful API uploads, upsert into 'cache_library'
        if successful_uploads:
            # We want to store the same clean structure in cache_library
            # Ensure the structure matches your 'cache_library' schema
            cache_entries = [
                {
                    "title": item.get("title"),
                    "authors": item.get("author"),
                    "isbn": item.get("isbn"),
                    "cover_url": item.get("cover_url"),
                    "total_pages": item.get("total_pages"),
                    "description": item.get("description")
                }
                for item in successful_uploads
            ]
            
            try:
                # Upsert to cache_library to ensure these are available for future users
                supabase.table("cached_library").upsert(cache_entries).execute()
                print(f"Successfully cached {len(cache_entries)} new books.")
            except Exception as e:
                print(f"Error updating cache_library: {e}")
        print(f"Supabase insert response: {response}")
