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
    update_currentbook,
    dnfbook,
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
        img = request.form.get("img", "")
        isbn = request.form.get("isbn", "")
        pages = request.form.get("pages", "0")

        # 4. Determine the user
        # We prioritize the 'user' passed in the form, fall back to session
        user = request.form.get("user") or session.get("display_name")

        if not user:
            return Response("User not identified", status=401)

        # 5. Save to your database
        add_book_to_library(user, title, author, isbn, img, int(pages))

        # 204 No Content is standard for successful HTMX requests
        # that don't need to swap HTML but need to trigger a refresh
        return Response(status=204, headers={"HX-Refresh": "true"})

    except json.JSONDecodeError:
        return Response("Invalid JSON format in 'data' field", status=400)
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
    user = session.get("display_name")
    dnfbook(user, bookid)
    # Here you would add logic to remove the book from the user's shelf in the database
    # For example: remove_book_from_shelf(user, bookid)
    return Response(status=204, headers={"HX-Refresh": "true"})


@api_bp.route("/currentbook", methods=["POST"])
def update_current_book():
    print(request.form)
    bookid = request.form["bookid"]
    user = session.get("display_name")
    update_currentbook(user, bookid)
    # Here you would add logic to remove the book from the user's shelf in the database
    # For example: remove_book_from_shelf(user, bookid)
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


@api_bp.route("/sendmsg", methods=["POST"])
def sendmsg():
    msgcontext = request.form
    return msgcontext
