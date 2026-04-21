from flask import (
    Flask,
    Response,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    send_from_directory,
)
from application.suggestions import (
    verify_token,
    app_callback,
    get_profile,
    create_playlist,
    clear_session,
    get_profile_data,
)
from application.logic import get_book_recommendations, get_playlist_recommendations
from application.database import (
    get_top_five_by_username,
    get_library,
    get_message_thread,
    get_messages,
    is_new,
)
import json, ast
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.template_folder = "../../templates"
app.static_folder = "../../static"

# Dummy user data
currentbook = {
    "author": "Stephen Graham Jones",
    "title": "Buffalo Hunter Hunter",
    "cover_url": "https://covers.openlibrary.org/b/id/14853611-L.jpg",
    "current_page": 150,
}
tbr = ["The Knight and The Moth", "Bury Our Bones In The Soil", "Our Infinite Fates"]
completed = ["Between Two Fires", "The Running Man", "Buffalo Hunter Hunter"]
dnf = ["Book A", "Book B"]


def organize_library(raw_data):
    """Sorts raw DB library data into status-based lists."""
    categories = {"reading": [], "completed": [], "dnf": [], "tbr": []}

    for book_data in raw_data:
        book_details = book_data.get("book", [])
        if not isinstance(book_details, list) or len(book_details) < 3:
            continue

        book_dict = {
            "id": book_data.get("id"),
            "title": book_details[0],
            "author": book_details[1],
            "cover_url": book_details[2],
            "status": book_data.get("status"),
            "pages": book_data.get("pages_read"),
            "total_pages": book_data.get("total_pages"),
        }

        status = book_dict["status"]
        if status in categories:
            categories[status].append(book_dict)
        else:
            categories["tbr"].append(book_dict)

    return categories


@app.route("/")
def index():

    return render_template("index.html")


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/allbooks")
def allbooks():
    data = get_library(session.get("user"))
    return data


@app.route("/api/getuserbook")
def get_user_book():
    user_id = request.args.get("user_id") or session.get("user")
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    data = get_library(user_id)
    return jsonify(data)


@app.route("/profile")
def profile():
    # Temporary hardcoded user for testing
    session["user"] = "wegotfight"  # This should be set during login/auth flow
    user_id = session.get("user")
    if not user_id:
        return render_template("profile.html", recs=[])

    # Fetch and organize library
    library_data = get_library(user_id)
    print(library_data)  # Using a test user for now
    sorted_books = organize_library(library_data)

    # Bot Profile Info (The account creating the playlists)
    bot_name = "wegotfight"
    bot_img = "https://www.creativefabrica.com/wp-content/uploads/2020/03/08/open-book-in-circle-icon-Graphics-3393563-1.jpg"

    profile_info = get_profile_data()  # Now uses Bot ID internally
    if profile_info:
        bot_name = profile_info.get("display_name", bot_name)
        bot_img = get_profile() or bot_img

    return render_template(
        "profile.html",
        img=bot_img,
        user=bot_name,
        currentbook=sorted_books["reading"],
        tbr=sorted_books["tbr"],
        completed=sorted_books["completed"],
        dnf=sorted_books["dnf"],
        recs=[],  # Add logic if needed
        messages=get_messages("wegotfight"),
    )


@app.route("/api/profile_data")
def api_profile_data():
    # 1. Get the user_id from the query parameters (e.g., ?user_id=123)
    # If not in params, check session (to keep it compatible with web)
    user_id = request.args.get("user_id") or session.get("user")

    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400

    # 2. Call your existing function from suggestions.py
    # This function uses get_spotify_client(user_id) which handles the token
    profile_data = get_profile_data(user_id)
    print(profile_data)
    if profile_data:
        return jsonify(profile_data)
    else:
        return jsonify({"error": "Could not fetch profile or unauthorized"}), 401


@app.route("/moretesting")
def moretesting():
    return render_template("moretesting.html")


@app.route("/profile/<user>")
def user_profile(user):
    # 1. Fetch library data (Returns a list of dictionaries from Supabase)
    tbr = get_library(user)
    print(f"Raw data from Supabase: {tbr}")

    better_data = []  # To Be Read (TBR)
    currentbook = []  # Currently Reading
    completed = []
    dnf = []

    # 2. Iterate over the list of dictionaries (book_data)
    for book_data in tbr:
        # Map Supabase column names to variables
        book_id = book_data.get("id")
        shelf_name = book_data.get("username")  # 'username' is the column name in DB
        book_details = book_data.get(
            "book"
        )  # This is already a Python list/dict (not a JSON string)
        status = book_data.get("status")
        pages_read = book_data.get("pages_read")
        total_pages = book_data.get("total_pages")
        version = book_data.get("version")

        # Ensure book_details is a list and has enough elements
        if not isinstance(book_details, list) or len(book_details) < 3:
            print(f"Skipping book ID {book_id} due to invalid or missing book details.")
            continue

        # Unpack the book details list
        title = book_details[0]
        author = book_details[1]
        cover_url = book_details[2]

        print(f"Processing book: {title}, Status: {status}")

        # Construct the standardized dictionary for rendering
        book_dict = {
            "id": book_id,
            "shelf": shelf_name,
            "title": title,
            "author": author,
            "cover_url": cover_url,
            "status": status,
            "version": version,
            "pages": pages_read,
            "total_pages": total_pages,
        }

        # 3. Sort the books into the appropriate lists
        if status == "reading":
            currentbook.append(book_dict)
        elif status == "completed":
            completed.append(book_dict)
        elif status == "dnf":
            dnf.append(book_dict)
        else:  # Assumed to be 'tbr' or uncategorized
            better_data.append(
                book_dict
            )  # better_data is used for TBR in the original code

    # --- Other data initialization (Kept from original) ---
    recs = get_top_five_by_username(user)

    # Assume get_profile_data() and get_profile() are defined elsewhere
    # And handle their potential absence gracefully.
    user = "Book Lover"
    img = "https://www.creativefabrica.com/wp-content/uploads/2020/03/08/open-book-in-circle-icon-Graphics-3393563-1.jpg"

    if session and callable(globals().get("get_profile_data")):
        profile_data = get_profile_data()
        if profile_data and profile_data.get("display_name"):
            user = profile_data["display_name"]

        if callable(globals().get("get_profile")):
            profile_img = get_profile()
            if profile_img:
                img = profile_img

    books = [  # This seems like placeholder data, keeping for consistency
        {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    ]
    # --- End other data initialization ---

    print(f"Current Book: {currentbook}")
    print(f"TBR: {better_data}")

    return render_template(
        "userprofile.html",
        img=img,
        books=books,
        user=user,
        currentbook=currentbook,
        tbr=better_data,
        completed=completed,
        dnf=dnf,
        recs=recs,
    )


@app.route("/friends")
def friends():
    return render_template("friends.html")


@app.route("/verify")
def verify():
    # Capture the platform (defaults to 'web' if not provided)
    platform = request.args.get("platform", "web")

    # We pass 'platform' into the Spotify 'state' parameter.
    # Spotify will pass this exact string back to our callback.
    auth_url = verify_token(platform)

    print(f"Initiating login for platform: {platform}")
    return redirect(auth_url)


@app.route("/api_callback")
def api_callback():
    # 1. Check the state parameter FIRST (before session might change)
    platform = request.args.get("state")

    # 2. Run your existing spotipy logic from suggestions.py
    # This handles the code exchange and populates the session
    app_callback(request)

    # 3. Get the user ID (now safely in the session from app_callback)
    user_id = session.get(
        "bot_user_id"
    )  # This is the ID your bot uses to fetch the token

    print(f"Callback received. Platform: {platform}, User: {user_id}")

    if platform == "flutter":
        # Redirect using the Custom Scheme to wake up the Flutter App
        # Ensure no spaces and correct host 'auth'
        return redirect(f"cadenceapp://auth?user_id={user_id}")

    # Default web behavior
    return redirect("/profile")


@app.route("/createplaylist")
def createplaylist():
    if session:
        playlist_id = create_playlist()
        return f"Playlist created! ID: {playlist_id}"


@app.route("/testgen", methods=["POST"])
def testgen():
    # Extract data from the Flutter POST request
    data_json = request.json
    author = data_json.get("author")
    title = data_json.get("title")
    image = data_json.get("cover")

    # Get the user_id (sent from Flutter)
    user_id = data_json.get("user_id") or session.get("user")

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    # 1. Get recommendations
    data, books = get_playlist_recommendations(data={"author": author, "title": title})

    # 2. Create the playlist using the specific user_id
    # Your suggestions.py create_playlist function already accepts user_id!
    playlist = create_playlist(data, books, image, user_id=user_id)

    print(f"Playlist created for {user_id}: {playlist}")
    return jsonify(playlist)


@app.route("/book/<booktitle>")
def book_page(booktitle):
    return f"This is the page for the book: {booktitle}"


@app.route("/<user>/tbr")
def user_tbr(user):
    if session.get("user") != user:
        return redirect(url_for("profile"))
    else:
        tbr = get_library(user)
        return jsonify(tbr)


@app.route("/completed/<user>")
def get_completed(user):
    completed = []
    tbr = get_library(user)
    for book in tbr:
        status = book.get("status")
        if status == "completed":
            completed.append(book)
        print(book)

    return render_template("completed.html", completed=completed)


@app.route("/roadmap")
def roadmap():
    return render_template("roadmap.html")


@app.route("/dbtest")
def dbtest():
    data = get_library()
    return {"data": data}


@app.route("/clear")
def clear():
    if session:
        session.clear()
        return redirect("/profile")
    else:
        return redirect("/profile")


@app.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="favicon.ico"))


@app.route("/app_version")
def app_version():
    print("Version check endpoint hit")
    # 1. FIXED: Corrected 'reponse' to 'response'
    # 2. FIXED: version_code is now an integer to match your Flutter int.parse()
    data = {
        "version_code": 10,
        "download_url": "https://mpmblozcvymuwujwvefy.supabase.co/storage/v1/object/public/cadence_storage/cadence.apk",
        "description": "Bug fixes and performance improvements!\nInitial Spotify Playlist integration - sample data from Project Hail Mary and Ludwig Goransson\n- Fixed a bug that caused the app to crash on startup for some users.\n- Improved loading times when fetching book recommendations.\n- Updated the user interface for a smoother experience.",
    }

    return Response(
        response=json.dumps(data),
        status=200,
        content_type="application/json",
    )
