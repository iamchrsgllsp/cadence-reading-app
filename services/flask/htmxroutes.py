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


@htmx_bp.route("/update_page", methods=["POST"])
def update_page():
    # 1. Safely retrieve form data, defaulting to None if key is missing.
    print(request.form)
    user_str = session.get("user")
    book_id_str = request.form["book_id"]
    current_page_str = request.form["current_page"]
    total_pages_str = request.form["total_pages"]
    if int(current_page_str) == int(total_pages_str):
        print("Congratulations on finishing the book!")
        complete_currentbook(user_str, book_id_str)

    # 2. Check for missing critical data first.
    if not book_id_str or not current_page_str:
        # Log error or handle gracefully
        current_app.logger.error("Missing book_id or current_page in form submission.")
        return "Error: Missing Data", 400

    # 3. Safely convert to integer only if the string is numeric.
    try:
        # If user_str is 'None', the int() conversion will fail,
        # so we convert to int only if the string is made of digits.
        user_id = user_str  # Assuming user_str is already the correct type
        book_id = int(book_id_str)
        current_page = int(current_page_str)

    except ValueError:
        # Log an error if the data cannot be converted to int (e.g., received "abc")
        current_app.logger.error(
            f"Invalid integer value received: user={user_str}, book={book_id_str}, page={current_page_str}"
        )
        return "Error: Invalid Data Type", 400

    # 4. Execute your update logic
    print(f"Updating user {user_id}, book {book_id} to page {current_page}")
    update_book_progress(user_id, book_id, current_page)
    print()
    # 5. Return the htmx success fragment (Status 200 is default)
    # Updated Python return statement

    # Final, clean Python return statement (Target is the success span)

    # --- SIMULATED PYTHON RETURN STRING (What /htmx/update_page should return) ---
    return f"""
    
<script>
    // This script runs immediately after the span is swapped into the DOM.
    window.location.reload();
</script>
"""
