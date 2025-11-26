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
    # print(request.form)
    data = ast.literal_eval(request.form["data"])
    print(data["key"])
    data = get_book_details_from_openlibrary(data["key"])
    print(data)
    book = [request.form["title"], request.form["author"], request.form["img"]]
    user = session.get("user")
    add_book_to_library(user, book, pages=data["page_count"])

    return Response(status=204, headers={"HX-Refresh": "true"})


@api_bp.route("/removefromshelf", methods=["POST"])
def remove_from_shelf():
    print(request.form)
    bookid = request.form["bookid"]
    user = session.get("user")
    remove_from_library(user, bookid)
    # Here you would add logic to remove the book from the user's shelf in the database
    # For example: remove_book_from_shelf(user, bookid)
    return Response(status=204, headers={"HX-Refresh": "true"})


@api_bp.route("/dnf", methods=["POST"])
def dnf():
    print(request.form)
    bookid = request.form["bookid"]
    user = session.get("user")
    dnfbook(user, bookid)
    # Here you would add logic to remove the book from the user's shelf in the database
    # For example: remove_book_from_shelf(user, bookid)
    return Response(status=204, headers={"HX-Refresh": "true"})


@api_bp.route("/currentbook", methods=["POST"])
def update_current_book():
    print(request.form)
    bookid = request.form["bookid"]
    user = session.get("user")
    update_currentbook(user, bookid)
    # Here you would add logic to remove the book from the user's shelf in the database
    # For example: remove_book_from_shelf(user, bookid)
    return Response(status=204, headers={"HX-Refresh": "true"})


@api_bp.route("/addtopfive", methods=["POST"])
def add_top_five():
    user = session.get("user")
    books = request.form.getlist("books[]")
    amend_top_five(
        user,
        books,
    )
    return {"data": "success"}
