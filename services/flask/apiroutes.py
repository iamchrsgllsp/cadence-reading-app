from flask import Blueprint, render_template, request, Response, session, jsonify
from application.logic import (
    fetch_data_from_api,
    process_data,
    get_book_details_from_openlibrary,
)
from application.database import (
    amend_top_five,
    add_book_to_library,
    remove_from_library,
    send_message,
    update_currentbook,
    dnfbook,
    get_messages,
)
import json
import ast

api_bp = Blueprint(
    "api", __name__, template_folder="../../templates", static_folder="../../static"
)


@api_bp.route("/hellothere")
def hellothere():
    return {"message": fetch_data_from_api("https://app.iamchrsg.dpdns.org/tester")}


@api_bp.route("/data")
def get_data():
    data = fetch_data_from_api("https://app.iamchrsg.dpdns.org/tester")
    processed = process_data(data)
    return {"processed_data": processed}


@api_bp.route("/addtolibrary", methods=["POST"])
def add_to_library():
    try:
        # 1. Get the 'data' string from the form and parse it as JSON
        # This replaces ast.literal_eval and works for Flutter & HTMX
        raw_data = request.form
        if not raw_data:
            return Response("Missing 'data' field", status=400)

        title = request.form.get("title", "Unknown Title")
        author = request.form.get("author", "Unknown Author")
        cover_url = request.form.get("img", "")
        isbn = request.form.get("isbn", "")
        pages = request.form.get("pages", "0")
        description = request.form.get("description", "No description available.")

        # 4. Determine the user
        # We prioritize the 'user' passed in the form, fall back to session
        if "Dart" in request.headers.get("User-Agent", ""):
            user = request.form.get("user")

        else:
            user = session.get("display_name")

        add_book_to_library(user, title, author, isbn, cover_url, pages, description)
        return Response(status=204, headers={"HX-Refresh": "true"})
    except Exception as e:
        # Log the actual error to your console for debugging
        print(f"Error in add_to_library: {e}")
        return Response("Internal Server Error", status=500)


@api_bp.route("/removefromshelf", methods=["POST"])
def remove_from_shelf():
    print(request.form)
    bookid = request.form["bookid"]
    user = session.get("display_name")
    remove_from_library(user, bookid)
    # Here you would add logic to remove the book from the user's shelf in the database
    # For example: remove_book_from_shelf(user, bookid)
    return Response(status=204, headers={"HX-Refresh": "true"})


@api_bp.route("/dnf", methods=["POST"])
def dnf():
    print(request.form)
    bookid = request.form["bookid"]
    if "Dart" in request.headers.get("User-Agent", ""):
        user = request.form.get("user")
        dnfbook(user, bookid)
        return jsonify(
            {
                "status": "success",
                "message": f"Book {bookid} set as current for user {user}",
            }
        )
    else:
        user = session.get("display_name")
        dnfbook(user, bookid)
        return Response(status=204, headers={"HX-Refresh": "true"})


@api_bp.route("/currentbook", methods=["POST"])
def update_current_book():
    print(request.form)
    bookid = request.form["bookid"]

    # Here you would add logic to remove the book from the user's shelf in the database
    # For example: remove_book_from_shelf(user, bookid)
    if "Dart" in request.headers.get("User-Agent", ""):
        user = request.form.get("user")
        update_currentbook(user, bookid)
        return jsonify(
            {
                "status": "success",
                "message": f"Book {bookid} set as current for user {user}",
            }
        )
    else:
        user = session.get("display_name")
        update_currentbook(user, bookid)
        return Response(status=204, headers={"HX-Refresh": "true"})


@api_bp.route("/addtopfive", methods=["POST"])
def add_top_five():
    # 1. Get the JSON data from the request body
    data = request.get_json()

    # Check if data was successfully parsed (good practice)
    if not data:
        return {"data": "invalid request body"}, 400

    # 2. Extract the 'top_five' list from the JSON object
    # The JS sends { top_five: currentRecsList }, so we look for 'top_five'
    books = data.get("top_five")

    # Check if the required key is present
    if books is None:
        return {"data": "missing 'top_five' key"}, 400

    # Get the user (as you were doing)
    user = session.get("display_name")

    # 3. Call your function with the extracted data
    amend_top_five(
        user,
        books,  # This 'books' variable now holds the data from currentRecsList
    )

    return {"data": "success"}


@api_bp.route("/submit_reply", methods=["POST"])
def sendmsg():
    if "Dart" in request.headers.get("User-Agent", ""):
        request_data = request.get_json()
        thread = request_data.get("thread")
        user = request_data.get("user")
        recipient = request_data.get("recipient")
        message = request_data.get("message")
    else:
        request_data = request.get_json()
        thread = request_data.get("thread")
        user = request_data.get("user")
        recipient = request_data.get("recipient")
        message = request_data.get("message")
    send_message(thread, user, recipient, message)
    return Response(status=204, headers={"HX-Refresh": "true"})


from flask import request, session, jsonify


@api_bp.route("/getmessages", methods=["GET"])
def get_messages_route():
    # 1. Determine the user and the token
    if "Dart" in request.headers.get("User-Agent", ""):
        # Flutter sends data via Headers and Args
        user = request.args.get("user")
        # Extract "Bearer <token>" from header
        auth_header = request.headers.get("Authorization")
        token = auth_header.split(" ")[1] if auth_header else None
    else:
        # Web uses the Flask session
        user = session.get("display_name")
        token = session.get("access_token")

    if not token:
        return jsonify({"error": "No token provided"}), 401

    # 2. Pass the token and user to your database function
    messages = get_messages(user, token)
    return jsonify(messages)
