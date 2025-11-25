import requests
import json
from application.genny import generate_with_gemini
import re
from collections import Counter
import statistics


def fetch_data_from_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def process_data(data):
    if not data:
        return "No data to process"
    # Example processing: just return the length of the data if it's a list
    if isinstance(data, list):
        return f"Data contains {len(data)} items."
    return f"Data is not a list, but of type {type(data)}."


def get_book_recommendations():
    data = [
        "The Knight and The Moth",
        "Bury Our Bones In The Soil",
        "Our Infinite Fates",
    ]
    prompt = (
        "Given the following list of books: "
        f"{data}. "
        "Please recommend 3 other books that share similar themes, genres, or writing styles. "
        "For each recommendation, briefly explain why it is similar."
        "Please format the response as a JSON array of objects, each containing 'title' and 'reason' fields."
    )
    books = generate_with_gemini(prompt=prompt)
    return books


def get_playlist_recommendations(data: dict):

    prompt = f"Act as a music recommendation engine, based on the following book: {data}, please provide a list of 20 songs that would fit the mood and themes of the book, try to make it mix of known songs as well as ambient/non vocal. Provide this in a JSON array format with each entry containing 'song_title' and 'artist' and 'spotify_id'."
    songs = generate_with_gemini(prompt=prompt)
    songs = songs.strip()
    songs = json.loads(songs)
    return data, songs


def get_book_details_from_openlibrary(olid: str):

    url = f"https://openlibrary.org/{olid}.json"
    data = fetch_data_from_api(url)
    if not data:
        return None

    title = data.get("title", "Unknown Title")

    # authors
    authors = data.get("authors", [])
    author_names = []
    for author in authors:
        author_key = author.get("author", {}).get("key")
        if author_key:
            author_data = fetch_data_from_api(
                f"https://openlibrary.org{author_key}.json"
            )
            if author_data:
                author_names.append(author_data.get("name", "Unknown Author"))

    # gather page counts from editions (number_of_pages or parse pagination)
    editions_url = f"https://openlibrary.org/{olid}/editions.json?limit=100"
    editions = fetch_data_from_api(editions_url)
    page_counts = []
    if editions and isinstance(editions, dict):
        for entry in editions.get("entries", []):
            # direct page count
            np = entry.get("number_of_pages")
            if isinstance(np, int) and np > 0:
                page_counts.append(np)
                continue

            # try parsing pagination string like "xviii, 312 p." or "312 pages"
            pagination = (
                entry.get("pagination")
                or entry.get("physical_dimensions")
                or entry.get("notes")
            )
            if isinstance(pagination, str):
                nums = re.findall(r"\d+", pagination)
                if nums:
                    try:
                        # choose the largest numeric token (commonly the page count)
                        pages = max(int(n) for n in nums)
                        if pages > 0:
                            page_counts.append(pages)
                    except Exception:
                        pass

    page_count = None
    if page_counts:
        # prefer the most common page count across editions, fallback to median
        try:
            page_count = Counter(page_counts).most_common(1)[0][0]
        except Exception:
            page_count = int(statistics.median(page_counts))

    result = {
        "title": title,
        "authors": author_names,
        "page_count": page_count,
        "page_counts_samples": sorted(set(page_counts))[:10],  # optional diagnostics
    }
    return result
