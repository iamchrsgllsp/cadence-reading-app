from flask import (
    Flask,
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
from application.database import get_top_five_by_username, get_library
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


@app.route("/profile")
def profile():
    # 1. Fetch library data (Returns a list of dictionaries from Supabase)
    tbr = get_library(session.get("user"))
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
    recs = get_top_five_by_username(session.get("user"))

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
        "profile.html",
        img=img,
        books=books,
        user=user,
        currentbook=currentbook,
        tbr=better_data,
        completed=completed,
        dnf=dnf,
        recs=recs,
    )


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


@app.route("/api_callback")
def api_callback():
    # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens if you reuse a SpotifyOAuth object
    app_callback(request)

    return redirect("/profile")


@app.route("/verify")
def verify():
    # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens if you reuse a SpotifyOAuth object
    auth_url = verify_token()
    print(auth_url)
    return redirect(auth_url)


@app.route("/createplaylist")
def createplaylist():
    if session:
        playlist_id = create_playlist()
        return f"Playlist created! ID: {playlist_id}"


@app.route("/testgen", methods=["POST"])
def testgen():
    author = request.json.get("author")
    title = request.json.get("title")
    image = request.json.get("cover")
    data, books = get_playlist_recommendations(data={"author": author, "title": title})
    playlist = create_playlist(data, books, image)
    print(playlist)
    # playlist = books
    return playlist


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
