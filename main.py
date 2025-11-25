import os
from dotenv import load_dotenv
from services.flask.routes import app
from services.flask.htmxroutes import htmx_bp
from services.flask.apiroutes import api_bp
from application.database import (
    get_db_connection,
    initialize_database,
    initialize_library,
)


# Load all variables from the .env file into os.environ
load_dotenv()

# Access the keys using os.environ.get()
gemini_key = os.environ.get("GEMINI_API_KEY")
spotify_id = os.environ.get("sid")
spotify_secret = os.environ.get("sid_sec")


if __name__ == "__main__":
    get_db_connection()
    initialize_database()
    initialize_library()
    app.register_blueprint(htmx_bp, url_prefix="/htmx")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.run(host="127.0.0.1", port=3000, debug=True)
