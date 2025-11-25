from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
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

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.template_folder = "../../templates"
app.static_folder = "../../static"

# Dummy user data
# currentbook = {"author":"Stephen Graham Jones","title":"Buffalo Hunter Hunter","cover_url":"https://covers.openlibrary.org/b/id/14853611-L.jpg","current_page":150}
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
    tbr = get_library(session.get("user"))
    print(tbr)
    better_data = []
    currentbook = []
    for (
        book_id,
        shelf_name,
        json_string,
        status,
        pages_read,
        total_pages,
        version,
    ) in tbr:
        # Decode the JSON string into a list of values
        book_details = json.loads(json_string)
        print(book_details[0], status)
        if status == "reading":
            currbook = {
                "id": book_id,
                "shelf": shelf_name,
                "title": book_details[0],
                "author": book_details[1],
                "cover_url": book_details[2],
                "status": status,
                "version": version,
                "pages": pages_read,
                "total_pages": total_pages,
            }
            currentbook.append(currbook)
        # Create a dictionary for the book
        book_dict = {
            "id": book_id,
            "shelf": shelf_name,
            "title": book_details[0],
            "author": book_details[1],
            "cover_url": book_details[2],
            "status": status,
            "version": version,
            "pages": pages_read,
            "total_pages": total_pages,
        }
        better_data.append(book_dict)
    recs = [
        [1, "The Knight and The Moth"],
        [2, "Twisted Window"],
        [3, "Between Two Fires"],
        [4, "Silver Nitrate"],
        [5, "Bury Our Bones In The Soil"],
    ]
    if session:
        user = get_profile_data()
        if user["display_name"]:
            user = user["display_name"]
    else:
        user = "Book Lover"
    books = [
        {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    ]
    if session:
        img = get_profile()
        if not img:
            img = "https://www.creativefabrica.com/wp-content/uploads/2020/03/08/open-book-in-circle-icon-Graphics-3393563-1.jpg"
    else:
        img = "https://www.creativefabrica.com/wp-content/uploads/2020/03/08/open-book-in-circle-icon-Graphics-3393563-1.jpg"
    print(currentbook)
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
    topfive = get_top_five_by_username(user)
    print(topfive[2])
    val = topfive[2]
    if isinstance(val, list):
        recs = val
    elif isinstance(val, str):
        # Try JSON first, then Python literal, then comma-split fallback
        try:
            recs = json.loads(val)
        except Exception:
            try:
                recs = ast.literal_eval(val)
            except Exception:
                recs = [s.strip() for s in val.split(",") if s.strip()]
    else:
        try:
            recs = list(val)
        except Exception:
            recs = [val]

    # ensure we always have a list
    if not isinstance(recs, list):
        recs = [recs]
    print(type(recs))
    return render_template(
        "userprofile.html",
        user=user,
        currentbook=currentbook,
        tbr=tbr,
        completed=completed,
        dnf=dnf,
        recs=recs,
    )


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
    data, books = get_playlist_recommendations(data={"author": author, "title": title})
    playlist = create_playlist(data, books)
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
