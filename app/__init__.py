import os
import logging
import json
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, request, session
from app.models import init_db
from .routes.auth import auth_bp, check_user
from .routes.admin import admin_bp
from .routes.gruppen import gruppen_bp
from .routes.mitgliederregistrierung import mitgliederregistrierung_bp
from .routes.profile import profile_bp
from .routes.index import index_bp

from dotenv import load_dotenv
load_dotenv()

def create_app():
    init_db()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

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
        "logs/app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())

    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    @app.context_processor
    def inject_user_permission():
        return dict(check_user=check_user)

    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def log_request(response):
        if request.path.startswith("/static"):
            return response

        duration = round((time.time() - request.start_time) * 1000, 2)

        app.logger.info(
            "HTTP Request",
            extra={
                "extra_data": {
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "ip": request.remote_addr,
                    "user_id": session.get("user_id"),
                    "duration_ms": duration
                }
            }
        )

        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(
            "Unhandled Exception",
            exc_info=True,
            extra={
                "extra_data": {
                    "method": request.method,
                    "path": request.path,
                    "ip": request.remote_addr,
                    "user_id": session.get("user_id")
                }
            }
        )
        return e

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(gruppen_bp)
    app.register_blueprint(mitgliederregistrierung_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(index_bp)

    return app
