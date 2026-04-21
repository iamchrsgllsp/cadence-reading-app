import os
import time
import spotipy
import requests
import base64
from flask import session
from spotipy.oauth2 import SpotifyOAuth, CacheHandler
from configfile import (
    spotify_id as sid,
    spotify_secret as sid_sec,
    bot_id as BOT_USER_ID,
)

from application.database import (
    add_full_token_info,
    save_img_to_db,
    get_supabase_client,
)

# Configuration
REDIRECT_URI = "https://cadence-reading-app.onrender.com/api_callback"
REDIRECT_URI2 = "http://127.0.0.1:3000/api_callback"
SCOPE = "user-read-recently-played, user-top-read, user-read-currently-playing, playlist-modify-public, ugc-image-upload"

# --- SUPABASE CACHE HANDLER ---


class SupabaseCacheHandler(CacheHandler):
    def __init__(self, user_id):
        self.user_id = user_id

    def get_cached_token(self):
        supabase = get_supabase_client()
        try:
            # .maybe_single() is cleaner for fetching one row
            res = (
                supabase.table("spotify_tokens")
                .select("access_token, refresh_token, expires_at, token_type, scope")
                .eq("user_id", self.user_id)
                .maybe_single()
                .execute()
            )
            return res.data if res.data else None
        except Exception as e:
            print(f"Error fetching token for {self.user_id}: {e}")
            return None

    def save_token_to_cache(self, token_info):
        supabase = get_supabase_client()
        try:
            payload = {
                "user_id": self.user_id,
                "access_token": token_info.get("access_token"),
                "refresh_token": token_info.get("refresh_token"),
                "expires_at": token_info.get("expires_at"),
                "token_type": token_info.get("token_type"),
                "scope": token_info.get("scope"),
            }
            # Ensure your DB has a unique constraint on user_id for upsert to work
            supabase.table("spotify_tokens").upsert(payload).execute()
        except Exception as e:
            print(f"Error saving token for {self.user_id}: {e}")


# --- CORE AUTH LOGIC ---


def get_spotify_oauth(handler=None):
    """Factory for SpotifyOAuth to ensure consistent config."""
    return SpotifyOAuth(
        client_id=sid,
        client_secret=sid_sec,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_handler=handler,
        cache_path=None,  # Disables local .cache file creation
        show_dialog=True,
    )


def get_spotify_client():
    """Always returns a client authenticated for the bot account."""
    # Use the persistent Bot ID instead of the session
    handler = SupabaseCacheHandler(BOT_USER_ID)
    sp_oauth = get_spotify_oauth(handler=handler)

    # validate_token automatically refreshes using the refresh_token
    # stored in Supabase if the current access_token is expired.
    cached_token = handler.get_cached_token()

    if not cached_token:
        print(
            f"CRITICAL: No token found for Bot {BOT_USER_ID}. Manual login required once."
        )
        return None

    token_info = sp_oauth.validate_token(cached_token)

    if not token_info:
        return None

    return spotipy.Spotify(auth=token_info["access_token"])


def verify_token(platform):
    """Generate auth URL; 'platform' state helps Flutter/Web routing logic."""
    sp_oauth = get_spotify_oauth()
    return sp_oauth.get_authorize_url(state=platform)


def app_callback(request):
    """Handles OAuth redirect and forces storage for the BOT_USER_ID."""
    sp_oauth = get_spotify_oauth()
    code = request.args.get("code")

    if not code:
        return session

    try:
        # 1. Get the token from Spotify using the auth code
        token_info = sp_oauth.get_access_token(code)

        # 2. Use the BOT_USER_ID handler specifically
        # This ensures the token is saved in the row the bot actually looks at
        handler = SupabaseCacheHandler(BOT_USER_ID)
        handler.save_token_to_cache(token_info)

        print(f"SUCCESS: Token saved for bot account {BOT_USER_ID}")

        # Optional: Sync session just for visual feedback in your UI
        session["bot_user_id"] = BOT_USER_ID

    except Exception as e:
        print(f"Callback error: {e}")

    return session


# --- HELPER FUNCTIONS ---


def spotify_search(sp, songs):
    """Search for tracks. Accepts 'sp' client to avoid redundant DB hits."""
    if not sp:
        return []

    results = []
    for song in songs:
        try:
            query = f"track:{song['song_title']} artist:{song['artist']}"
            search_result = sp.search(q=query, type="track", limit=1)
            items = search_result.get("tracks", {}).get("items", [])

            if items:
                results.append(
                    {
                        "song_title": song["song_title"],
                        "artist": song["artist"],
                        "spotify_id": items[0]["id"],
                    }
                )
        except Exception as e:
            print(f"Search error for {song.get('song_title')}: {e}")
    return results


def create_playlist(book, songs, cover_url):
    sp = get_spotify_client()
    if not sp:
        return None

    try:
        # Create playlist under the bot's account
        playlist = sp.user_playlist_create(
            user=BOT_USER_ID,
            name=f"cadence - {book['title']}",
            public=True,
            description=f"Playlist for: {book['title']} by {book['author']}",
        )

        # ... rest of your track search and addition logic remains the same ...
        playlist_id = playlist["id"]
        found_tracks = spotify_search(sp, songs)
        track_uris = [f"spotify:track:{t['spotify_id']}" for t in found_tracks]

        if track_uris:
            sp.playlist_add_items(playlist_id=playlist_id, items=track_uris[:100])

        if cover_url:
            upload_playlist_cover(sp, playlist_id, cover_url)

        return {"playlist_id": playlist_id}
    except Exception as e:
        print(f"Playlist creation error: {e}")
        return None


def upload_playlist_cover(sp, playlist_id, cover_url):
    """Helper to handle Spotify's picky image requirements."""
    try:
        # 1. Get the actual image URL from your DB tool
        final_img_url = save_img_to_db(cover_url)
        resp = requests.get(final_img_url)

        if resp.status_code == 200:
            # Spotify limit is ~256KB. If your images are huge, this will fail.
            if len(resp.content) > 250000:
                print("Warning: Image too large for Spotify cover.")
                return

            b64_img = base64.b64encode(resp.content).decode("utf-8")
            sp.playlist_upload_cover_image(playlist_id, b64_img)
    except Exception as e:
        print(f"Cover upload error: {e}")


def get_profile_data():
    """Fetches full Spotify profile dictionary."""

    sp = get_spotify_client()

    print(f"DEBUG: get_profile_data - Spotify client: {sp}")

    if not sp:

        return None

    try:

        return sp.current_user()

    except Exception as e:

        print(f"Error fetching profile data: {e}")

        return None


def get_profile(user_id=None):
    """
    Get user's Spotify profile picture.

    Args:
        user_id: Unique identifier for the user. If None, uses current session user.

    Returns:
        Profile image URL or None
    """

    sp = get_spotify_client()

    if not sp:
        return None

    try:
        data = sp.current_user()
        session["user"] = data["id"]
        print("Fetched user profile:", data["id"])

        # Return profile image if available
        if data.get("images") and len(data["images"]) > 1:
            return data["images"][1]["url"]
        elif data.get("images") and len(data["images"]) > 0:
            return data["images"][0]["url"]

        return None
    except Exception as e:
        print(f"Error fetching profile for user {user_id}: {e}")
        return None


def clear_session(user_id=None):
    """
    Clear session data for a specific user or all users.

    Args:
        user_id: If provided, clears only that user's data. Otherwise clears all.

    Returns:
        session object
    """
    if user_id:
        handler = SupabaseCacheHandler(user_id)
        token_key = handler.get_token_key(user_id)
        session.pop(token_key, None)
        if session.get("user") == user_id:
            session.pop("user", None)

    return session
