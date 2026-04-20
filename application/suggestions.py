import os
import time
import spotipy
import requests
import base64
from flask import session
from spotipy.oauth2 import SpotifyOAuth, CacheHandler
from configfile import spotify_id as sid, spotify_secret as sid_sec

# Import your database tools
# Ensure 'supabase' is initialized in your application.database file
from application.database import add_full_token_info, save_img_to_db, supabase

# Configuration
REDIRECT_URI = "https://cadence-reading-app.onrender.com/api_callback"
SCOPE = "user-read-recently-played, user-top-read, user-read-currently-playing, playlist-modify-public, ugc-image-upload"

# --- NEW: SUPABASE CACHE HANDLER ---


class SupabaseCacheHandler(CacheHandler):
    """
    Custom handler to store and retrieve Spotify tokens from Supabase.
    This allows Flutter to access tokens without a browser session.
    """

    def __init__(self, user_id):
        self.user_id = user_id

    def get_cached_token(self):
        try:
            # Query your tokens table
            res = (
                supabase.table("spotify_tokens")
                .select("*")
                .eq("user_id", self.user_id)
                .execute()
            )
            if res.data:
                # Return the first row as a dictionary
                return res.data[0]
        except Exception as e:
            print(f"Error fetching token from Supabase for {self.user_id}: {e}")
        return None

    def save_token_to_cache(self, token_info):
        try:
            # Prepare payload matching your table columns
            payload = {
                "user_id": self.user_id,
                "access_token": token_info.get("access_token"),
                "refresh_token": token_info.get("refresh_token"),
                "expires_at": token_info.get("expires_at"),
                "token_type": token_info.get("token_type"),
                "scope": token_info.get("scope"),
            }
            # Upsert will update the record if user_id exists, otherwise insert
            supabase.table("spotify_tokens").upsert(payload).execute()
            print(f"Token synced to Supabase for user: {self.user_id}")
        except Exception as e:
            print(f"Error saving token to Supabase for {self.user_id}: {e}")


# --- CORE LOGIC REFACTOR ---


def get_spotify_oauth():
    """Create a standard SpotifyOAuth instance."""
    return spotipy.oauth2.SpotifyOAuth(
        client_id=sid,
        client_secret=sid_sec,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
    )


def get_spotify_client(user_id=None):
    """
    Main entry point for getting an authenticated Spotify client.
    Works for both Web (session) and Flutter (explicit user_id).
    """
    # Fallback to session if no user_id is provided (for web users)
    if not user_id:
        user_id = session.get("user")

    if not user_id:
        print("DEBUG: get_spotify_client failed - no user_id available.")
        return None

    # Use our custom Supabase handler to bypass local .cache files
    handler = SupabaseCacheHandler(user_id)

    sp_oauth = SpotifyOAuth(
        client_id=sid,
        client_secret=sid_sec,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_handler=handler,
    )

    # validate_token automatically checks 'expires_at' and uses the
    # 'refresh_token' to update Supabase if the token is old.
    token_info = sp_oauth.validate_token(handler.get_cached_token())

    if not token_info:
        print(f"DEBUG: No valid token found in Supabase for user {user_id}")
        return None

    return spotipy.Spotify(auth=token_info["access_token"])


def verify_token(platform):
    """Generate Spotify authorization URL with platform state."""
    sp_oauth = get_spotify_oauth()
    # Passing platform in 'state' ensures it survives the redirect
    auth_url = sp_oauth.get_authorize_url(state=platform)
    return auth_url


def app_callback(request):
    """Handles the Spotify OAuth callback and saves the result to Supabase."""
    sp_oauth = get_spotify_oauth()
    code = request.args.get("code")

    if not code:
        return session

    try:
        # 1. Exchange code for token
        token_info = sp_oauth.get_access_token(code)

        # 2. Identify the user
        temp_sp = spotipy.Spotify(auth=token_info.get("access_token"))
        user_data = temp_sp.current_user()
        user_id = user_data["id"]

        # 3. Save to Session (for Web)
        session["user"] = user_id

        # 4. Save to Supabase (for Flutter/Persistence)
        handler = SupabaseCacheHandler(user_id)
        handler.save_token_to_cache(token_info)

        print(f"User {user_id} fully authenticated and synced to Supabase.")

    except Exception as e:
        print(f"Callback error: {e}")

    return session


# --- HELPER FUNCTIONS ---


def get_profile_data(user_id=None):
    """Fetches full Spotify profile dictionary."""
    sp = get_spotify_client(user_id)
    if not sp:
        return None
    try:
        return sp.current_user()
    except Exception as e:
        print(f"Error fetching profile data: {e}")
        return None


def create_playlist(book, songs, cover, user_id=None):
    """Creates a Spotify playlist and uploads a custom cover."""
    sp = get_spotify_client(user_id)
    if not sp:
        return None

    try:
        spotify_user_id = sp.current_user()["id"]

        playlist = sp.user_playlist_create(
            user=spotify_user_id,
            name=f"cadence - {book['title']}",
            public=True,
            description=f"Playlist for: {book['title']} by {book['author']}",
        )

        playlist_id = playlist["id"]
        track_uris = [
            f"spotify:track:{t['spotify_id']}"
            for t in spotify_search(songs, user_id)
            if "spotify_id" in t
        ]

        if track_uris:
            sp.playlist_add_items(playlist_id=playlist_id, items=track_uris)

        if cover:
            try:
                # Convert URL to base64 for Spotify
                img_url = save_img_to_db(cover)
                resp = requests.get(img_url)
                if resp.status_code == 200:
                    b64_img = base64.b64encode(resp.content).decode("utf-8")
                    sp.playlist_upload_cover_image(playlist_id, b64_img)
            except Exception as e:
                print(f"Cover upload error: {e}")

        return {"playlist_id": playlist_id}
    except Exception as e:
        print(f"Playlist creation error: {e}")
        return None


def spotify_search(songs, user_id=None):
    """Search for tracks and return their Spotify IDs."""
    sp = get_spotify_client(user_id)
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
