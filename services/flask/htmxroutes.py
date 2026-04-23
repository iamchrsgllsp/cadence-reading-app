from flask import Blueprint, render_template, request, session
import requests
from application.database import (
    amend_top_five,
    update_book_progress,
    complete_currentbook,
)

htmx_bp = Blueprint(
    "htmx", __name__, template_folder="../../templates", static_folder="../../static"
)


@htmx_bp.route("/hellothere")
def hellothere():
    from datetime import datetime

    now = datetime.now().strftime("%H:%M:%S")
    return f"""<div
    hx-get="/htmx/hellothere"
    hx-trigger="every 2s"
    hx-swap="outerHTML"
><h1>More Testing Page</h1>
<h1>The time is {now}</h1></div>"""


@htmx_bp.route("/posttest", methods=["POST"])
def htmxposting():
    print(request.form["message"])
    return """
    <div id="post-success" style="background: #d4edda; padding: 10px; border-radius: 5px;">
        You posted to the server!
        <script>
            setTimeout(function() {
                var el = document.getElementById('post-success');
                if (el) el.style.display = 'none';
            }, 3000);
        </script>
    </div>
    """


@htmx_bp.route("/search", methods=["GET"])
def htmx_search():
    query = request.args.get("search")
    print(f"Search query: {query}")
    url = f"https://openlibrary.org/search.json?q={query}"
    response = requests.get(url)
    data = response.json()
    books = data.get("docs", [])[:10]  # Get first 10 results
    print(books)
    return render_template("htmx_search.html", books=books)


from flask import request, current_app


from flask import request, current_app, jsonify


@htmx_bp.route("/update_page", methods=["POST"])
def update_page():
    # 1. Extract Data
    user_id = request.form.get("user_id")
    book_id_str = request.form.get("book_id")
    current_page_str = request.form.get("current_page")
    total_pages_str = request.form.get("total_pages")

    # 2. Validation Logic
    if not all([user_id, book_id_str, current_page_str]):
        return "Missing Data", 400

    try:
        book_id = int(book_id_str)
        current_page = int(current_page_str)

        # Perform the actual update
        update_book_progress(user_id, book_id, current_page)

        if current_page == int(total_pages_str or 0):
            complete_currentbook(user_id, book_id)

    except ValueError:
        return "Invalid Data Type", 400

    # 3. Conditional Return based on Header
    # Check if it's an HTMX request
    if request.headers.get("HX-Request"):
        return """
        <script>
            window.location.reload();
        </script>
        """

    # Check if it's coming from a Dart/Flutter client
    user_agent = request.headers.get("User-Agent", "")
    if "Dart" in user_agent or request.accept_mimetypes.accept_json:
        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Book {book_id} updated to page {current_page}",
                    "user_id": user_id,
                }
            ),
            200,
        )

    # Default fallback
    return "Update Successful", 200
