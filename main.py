from services.flask.routes import app
from services.flask.htmxroutes import htmx_bp
from services.flask.apiroutes import api_bp
from application.database import (
    get_db_connection,
    initialize_database,
    initialize_library,
)
import os
from dotenv import load_dotenv

load_dotenv()

# Access the keys using os.environ.get()
gemini_key = os.environ.get("GEMINI_API_KEY")
spotify_id = os.environ.get("sid")
spotify_secret = os.environ.get("sid_sec")
print("Environment variables loaded:")
print("GEMINI_API_KEY:", gemini_key)
print("Spotify ID:", spotify_id)
print("Spotify Secret:", spotify_secret)


# Load all variables from the .env file into os.environ
get_db_connection()
initialize_database()
initialize_library()
app.register_blueprint(htmx_bp, url_prefix="/htmx")
app.register_blueprint(api_bp, url_prefix="/api")


if __name__ == "__main__":

    app.run(host="127.0.0.1", port=3000, debug=True)
