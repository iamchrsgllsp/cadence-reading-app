from services.flask.routes import app
from services.flask.htmxroutes import htmx_bp
from services.flask.apiroutes import api_bp


"""
from application.database import (
    get_db_connection,
    initialize_database,
    initialize_library,
)
"""

# Load all variables from the .env file into os.environ

"""
get_db_connection()
initialize_database()
initialize_library()
"""
app.register_blueprint(htmx_bp, url_prefix="/htmx")
app.register_blueprint(api_bp, url_prefix="/api")


if __name__ == "__main__":

    app.run(host="127.0.0.1", port=3000, debug=True)
