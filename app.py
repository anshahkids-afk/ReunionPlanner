from flask import Flask
from config import FLASK_SECRET_KEY
from access_routes import access_bp
from board_routes import board_bp


def format_time_12h(value):
    """'18:00:00' or '18:00' -> '6:00 PM'. Falls back to the raw value."""
    if not value:
        return ""
    try:
        parts = str(value).split(":")
        hour, minute = int(parts[0]), int(parts[1])
        period = "AM" if hour < 12 else "PM"
        display_hour = hour % 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{minute:02d} {period}"
    except (ValueError, IndexError):
        return str(value)


def create_app():
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY

    app.register_blueprint(access_bp)
    app.register_blueprint(board_bp)

    app.jinja_env.filters["time12"] = format_time_12h

    @app.context_processor
    def inject_globals():
        from flask import session
        return {"current_name": session.get("name")}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
