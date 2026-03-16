import json
import logging
import os
import time
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_login import LoginManager, current_user

from app.models import User, get_accounts, init_db

from .routes.admin import admin_bp
from .routes.auth import auth_bp
from .routes.gruppen import gruppen_bp
from .routes.index import index_bp
from .routes.mitglieder import mitglieder_bp
from .routes.profile import profile_bp

login_manager = LoginManager()
login_manager.login_view = "auth.login"
load_dotenv()


def create_app():
    init_db()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SECURE=True,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=72),
    )

    login_manager.init_app(app)

    if not os.path.exists("logs"):
        os.mkdir("logs")

    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
            }
            if hasattr(record, "extra_data"):
                log_record.update(record.extra_data)
            if record.exc_info:
                log_record["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_record)

    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def log_request(response):
        if request.path.startswith("/static"):
            return response

        duration = round((time.time() - request.start_time) * 1000, 2)
        user_info = {
            "user_id": getattr(current_user, "id", None),
            "username": getattr(current_user, "username", None),
            "role": getattr(current_user, "role", None),
        }

        log_data = {
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "ip": request.remote_addr,
            "duration_ms": duration,
            "user": user_info,
        }

        if 400 <= response.status_code < 500:
            app.logger.warning("Client error", extra={"extra_data": log_data})
        elif response.status_code >= 500:
            app.logger.error("Server error", extra={"extra_data": log_data})
        else:
            app.logger.info("HTTP Request", extra={"extra_data": log_data})

        return response

    @app.errorhandler(403)
    def forbidden(_e):
        user_info = {
            "user_id": getattr(current_user, "id", None),
            "username": getattr(current_user, "username", None),
            "role": getattr(current_user, "role", None),
        }
        app.logger.warning(
            "Forbidden access",
            extra={
                "extra_data": {
                    "method": request.method,
                    "path": request.path,
                    "ip": request.remote_addr,
                    "user": user_info,
                }
            },
        )
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(_e):
        user_info = {
            "user_id": getattr(current_user, "id", None),
            "username": getattr(current_user, "username", None),
            "role": getattr(current_user, "role", None),
        }
        app.logger.warning(
            "Page not found",
            extra={
                "extra_data": {
                    "method": request.method,
                    "path": request.path,
                    "ip": request.remote_addr,
                    "user": user_info,
                }
            },
        )
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(_e):
        user_info = {
            "user_id": getattr(current_user, "id", None),
            "username": getattr(current_user, "username", None),
            "role": getattr(current_user, "role", None),
        }
        app.logger.error(
            "Server error",
            exc_info=True,
            extra={
                "extra_data": {
                    "method": request.method,
                    "path": request.path,
                    "ip": request.remote_addr,
                    "user": user_info,
                }
            },
        )
        return render_template("errors/500.html"), 500

    @login_manager.user_loader
    def load_user(user_id):
        with get_accounts() as conn:
            row = conn.execute(
                "SELECT id, uname, role FROM accounts WHERE id=?", (user_id,)
            ).fetchone()

        if row:
            return User(row["id"], row["uname"], row["role"])

        return None

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(gruppen_bp)
    app.register_blueprint(mitglieder_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(index_bp)

    return app
