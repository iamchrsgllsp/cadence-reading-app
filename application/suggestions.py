import time
import spotipy
from flask import session
import requests
import base64
from configfile import spotify_id as sid, spotify_secret as sid_sec
from application.overlay import create_playlist_image
from application.database import add_full_token_info

REDIRECT_URI = "https://cadence-reading-app.onrender.com/api_callback"
API_BASE = "https://accounts.spotify.com"
SCOPE = "user-read-recently-played, user-top-read, user-read-currently-playing,playlist-modify-public,ugc-image-upload"


def get_user_token_key(user_id):
    """Generate a unique session key for a user's token."""
    return f"token_info_{user_id}"


def get_current_user_id():
    """Get the current user's ID from session."""
    return session.get("user")


def get_spotify_oauth():
    """Create a SpotifyOAuth instance."""
    return spotipy.oauth2.SpotifyOAuth(
        client_id=sid,
        client_secret=sid_sec,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
    )


def get_token_info(user_id=None):
    """
    Get and refresh token for a specific user.

    Args:
        user_id: Unique identifier for the user. If None, uses current session user.

    Returns:
        tuple: (token_info dict or None, is_valid boolean)
    """
    # If no user_id provided, get from session
    if not user_id:
        user_id = get_current_user_id()

    if not user_id:
        return None, False

    # Get user-specific token from session
    token_key = get_user_token_key(user_id)
    token_info = session.get(token_key)

    # 1. Check for initial token existence
    if not token_info:
        return None, False

    # Safely check for required keys
    expires_at = token_info.get("expires_at")
    refresh_token = token_info.get("refresh_token")

    if not expires_at or not refresh_token:
        return None, False

    # 2. Check for token expiration (with a 60-second buffer)
    now = int(time.time())
    is_token_expired = expires_at - now < 60

    # 3. Refresh token if expired
    if is_token_expired:
        try:
            sp_oauth = get_spotify_oauth()
            new_token_info = sp_oauth.refresh_access_token(refresh_token)

            # Update the session with the new token info
            session[token_key] = new_token_info
            token_info = new_token_info

            # Update token in database
            add_full_token_info(user_id, new_token_info)

        except Exception as e:
            print(f"Token refresh failed for user {user_id}: {e}")
            session.pop(token_key, None)
            return None, False

    return token_info, True


def get_spotify_client(user_id=None):
    """
    Get an authenticated Spotify client for a specific user.

    Args:
        user_id: Unique identifier for the user. If None, uses current session user.

    Returns:
        Spotify client or None if authentication fails
    """
    token_info, is_valid = get_token_info(user_id)

    if not is_valid or not token_info:
        return None

    return spotipy.Spotify(auth=token_info.get("access_token"))


def verify_token():
    """Generate Spotify authorization URL."""
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return auth_url


def app_callback(request):
    """
    Handle Spotify OAuth callback.

    Args:
        request: Flask request object with authorization code

    Returns:
        session object
    """
    sp_oauth = get_spotify_oauth()
    code = request.args.get("code")

    if not code:
        return session

    try:
        # Get token info from authorization code
        token_info = sp_oauth.get_access_token(code)

        # Get user profile to identify the user
        sp = spotipy.Spotify(auth=token_info.get("access_token"))
        user_data = sp.current_user()
        user_id = user_data["id"]

        # Store token with user-specific key
        token_key = get_user_token_key(user_id)
        session[token_key] = token_info
        session["user"] = user_id

        # Add token to database
        add_full_token_info(user_id, token_info)

        print(f"User {user_id} authenticated successfully")

    except Exception as e:
        print(f"Callback error: {e}")

    return session


def get_profile(user_id=None):
    """
    Get user's Spotify profile picture.

    Args:
        user_id: Unique identifier for the user. If None, uses current session user.

    Returns:
        Profile image URL or None
    """
    if not user_id:
        user_id = get_current_user_id()

    sp = get_spotify_client(user_id)

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


def get_profile_data(user_id=None):
    """
    Get full user profile data.

    Args:
        user_id: Unique identifier for the user. If None, uses current session user.

    Returns:
        User profile data dict or None
    """
    sp = get_spotify_client(user_id)

    if not sp:
        return None

    try:
        return sp.current_user()
    except Exception as e:
        print(f"Error fetching profile data: {e}")
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
        token_key = get_user_token_key(user_id)
        session.pop(token_key, None)
        if session.get("user") == user_id:
            session.pop("user", None)
    else:
        session.clear()

    return session


def create_playlist(book, songs, user_id=None):
    """
    Create a Spotify playlist for a book.

    Args:
        book: Book dictionary with title, author, and cover_url
        songs: List of song dictionaries
        user_id: Unique identifier for the user. If None, uses current session user.

    Returns:
        Dictionary with playlist_id or None
    """
    sp = get_spotify_client(user_id)

    if not sp:
        print("Failed to get Spotify client")
        return None

    try:
        spotify_user_id = sp.current_user()["id"]

        # 1. Create the playlist
        playlist = sp.user_playlist_create(
            user=spotify_user_id,
            name=f"cadence - {book['title']}",
            public=True,
            description=f"CADENCE recommended playlist for: {book['title']} by {book['author']}",
        )

        playlist_id = playlist["id"]
        print(f"Created playlist: {playlist_id}")

        # 2. Search for tracks and get Spotify IDs
        track_uris = spotify_search(songs, user_id)
        track_uris = [
            f"spotify:track:{track['spotify_id']}"
            for track in track_uris
            if "spotify_id" in track
        ]

        # 3. Add tracks to playlist
        if track_uris:
            try:
                sp.playlist_add_items(playlist_id=playlist_id, items=track_uris)
                print(f"Added {len(track_uris)} tracks to playlist")
            except Exception as e:
                print(f"Error adding tracks to playlist {playlist['name']}: {e}")

        # 4. Add custom cover image
        image_url = book.get("cover_url")
        if image_url:
            try:
                image_url = create_playlist_image(image_url)
                response = requests.get(
                    "https://i.postimg.cc/T3q8m6Dg/composite-image.jpg"
                )

                if response.status_code == 200:
                    image_data = base64.b64encode(response.content).decode("utf-8")
                    sp.playlist_upload_cover_image(playlist_id, image_data)
                    print("Uploaded custom cover image")
                else:
                    print(f"Failed to fetch cover image from {image_url}")
            except Exception as e:
                print(f"Error uploading cover image: {e}")

        return {"playlist_id": playlist_id}

    except Exception as e:
        print(f"Error creating playlist: {e}")
        return None


def spotify_search(songs, user_id=None):
    """
    Search for songs on Spotify.

    Args:
        songs: List of song dictionaries with song_title and artist
        user_id: Unique identifier for the user. If None, uses current session user.

    Returns:
        List of dictionaries with song info and Spotify IDs
    """
    sp = get_spotify_client(user_id)

    if not sp:
        print("Failed to get Spotify client for search")
        return []

    results = []
    for song in songs:
        try:
            query = f"track:{song['song_title']} artist:{song['artist']}"
            search_result = sp.search(q=query, type="track", limit=1)
            items = search_result.get("tracks", {}).get("items", [])

            if items:
                track = items[0]
                results.append(
                    {
                        "song_title": song["song_title"],
                        "artist": song["artist"],
                        "spotify_id": track["id"],
                    }
                )
            else:
                print(f"No results found for {song['song_title']} by {song['artist']}")
        except Exception as e:
            print(f"Error searching for {song.get('song_title', 'unknown')}: {e}")

    return results
