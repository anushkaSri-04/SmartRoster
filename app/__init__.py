
import os

from dotenv import load_dotenv
from flask import Flask
from app import models
from app.config import Config
from app.extensions import db, migrate


def create_app(test_config=None):

    # Load environment variables
    load_dotenv()

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Allow test-specific configuration
    if test_config:
        app.config.update(test_config)

    # Normalize PostgreSQL URL for Psycopg 3
    database_url = app.config["SQLALCHEMY_DATABASE_URI"]

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1
        )

    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so migrations can detect them
    from app import models

    # Register routes
    from app.routes import main

    app.register_blueprint(main)

    return app
