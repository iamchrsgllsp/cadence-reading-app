import time
import spotipy
from flask import session
import requests
import base64
from configfile import spotify_id as sid, spotify_secret as sid_sec
from application.overlay import create_playlist_image

# shift the sid to a config file later


# REDIRECT_URI2 = "http://127.0.0.1:3000/api_callback"
REDIRECT_URI = "https://cadence-reading-app.onrender.com/api_callback"
API_BASE = "https://accounts.spotify.com"
SCOPE = "user-read-recently-played, user-top-read, user-read-currently-playing,playlist-modify-public,ugc-image-upload"


import time
from flask import session  # Assuming you pass the session object from Flask

# Note: Your constants (sid, sid_sec, REDIRECT_URI, SCOPE)
# must be defined globally or passed in.


def get_token_info(session):
    if session:
        token_info = session.get("token_info")

    # 1. Check for initial token existence
    if not token_info:
        # User has not authenticated yet
        return None, False

    # Safely check for required keys
    expires_at = token_info.get("expires_at")
    refresh_token = token_info.get("refresh_token")

    if not expires_at or not refresh_token:
        # Token data is incomplete/malformed
        return None, False

    # 2. Check for token expiration (with a 60-second buffer)
    now = int(time.time())
    is_token_expired = expires_at - now < 60

    # 3. Refreshing token if it has expired
    if is_token_expired:
        try:
            # Initialize SpotifyOAuth object
            sp_oauth = spotipy.oauth2.SpotifyOAuth(
                sid,
                sid_sec,
                REDIRECT_URI,
                scope=SCOPE,
            )

            # Perform the refresh
            new_token_info = sp_oauth.refresh_access_token(refresh_token)

            # CRITICAL: Update the session with the new token info
            session["token_info"] = new_token_info
            token_info = new_token_info  # Use the new token_info for the return

        except Exception as e:
            # Handle refresh failure (e.g., revoked permissions)
            print(f"Token refresh failed: {e}")
            session.pop("token_info", None)  # Clear invalid token data
            return None, False

    # Token is valid or has just been successfully refreshed
    return token_info, True


def verify_token():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(
        client_id=sid, client_secret=sid_sec, redirect_uri=REDIRECT_URI, scope=SCOPE
    )
    auth_url = sp_oauth.get_authorize_url()
    return auth_url


def app_callback(request):
    sp_oauth = spotipy.oauth2.SpotifyOAuth(
        client_id=sid, client_secret=sid_sec, redirect_uri=REDIRECT_URI, scope=SCOPE
    )
    session.clear()
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    # Saving the access token along with all other token related info
    session["token_info"] = token_info
    return session


def get_profile():
    sp = spotipy.Spotify(auth=session.get("token_info").get("access_token"))
    data = sp.current_user()
    session["user"] = data["id"]
    print("Fetched user profile:", data["id"])
    return data["images"][1]["url"]


def get_profile_data():
    sp = spotipy.Spotify(auth=session.get("token_info").get("access_token"))
    data = sp.current_user()
    return data


def clear_session():
    session.clear()
    return session


def create_playlist(book, songs):
    sp = spotipy.Spotify(auth=session.get("token_info").get("access_token"))
    user_id = sp.current_user()["id"]

    # 1. Create the playlist
    playlist = sp.user_playlist_create(
        user=user_id,
        name=f"cadence - {book['title']}",
        public=True,
        description=f"CADENCE recommended playlist for: {book['title']} by {book['author']}",
    )

    playlist_id = playlist["id"]
    print(songs)
    # 2. Extract all valid Spotify URIs/IDs
    # **Crucial step**: Ensure song['spotify_id'] is the correct track URI (e.g., 'spotify:track:...')
    track_uris = spotify_search(songs)
    track_uris = [
        f"spotify:track:{track['spotify_id']}"
        for track in track_uris
        if "spotify_id" in track
    ]
    # 3. Batch add all items at once (or in chunks if > 100, but one call is best here)
    if track_uris:
        # The spotipy method can handle a list of URIs/IDs.
        # It's much faster and reliable than looping.
        try:
            sp.playlist_add_items(playlist_id=playlist_id, items=track_uris)
        except Exception as e:
            print(f"Error adding tracks to playlist {playlist['name']}: {e}")
    image_url = book.get("cover_url")
    image_url = create_playlist_image(image_url)
    if image_url:
        response = requests.get("https://i.postimg.cc/T3q8m6Dg/composite-image.jpg")
        if response.status_code == 200:
            image_data = base64.b64encode(response.content).decode("utf-8")

            sp.playlist_upload_cover_image(playlist_id, image_data)
        else:
            print(f"Failed to fetch cover image from {image_url}")
    return {"playlist_id": playlist_id}


def spotify_search(songs):
    sp = spotipy.Spotify(auth=session.get("token_info").get("access_token"))
    results = []
    for song in songs:
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
    return results
