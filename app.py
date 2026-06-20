from dbm import sqlite3
import os
import secrets

from flask import Flask
from dotenv import load_dotenv
from sqlalchemy import Engine, StaticPool, event
import sqlite3

from odontocare.admin.bp_admin import bp_users
from odontocare.admin.auth import bp_auth
from odontocare.appointments.bp_appointments import bp_appointments

from db_init import db

# load_dotenv()

def create_app():
    """
        Initialise Flask application and its database
    """

    # Activate foreign key for SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()
        
    app = Flask("OdontoCare")

    # Configure SQLite in-memory database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool
    }
    app.config["JWT_SECRET_KEY"] = secrets.token_hex(32)
    
    # Initialise Flask app
    db.init_app(app)

    with app.app_context():
        from odontocare.admin.db_admin import User

        # Create tables
        db.create_all()

        # Load Administrator user
        admin_user = User(usr_name=os.getenv("ADMIN_USR"), usr_pwd=os.getenv("ADMIN_PWD"), usr_role=os.getenv("ADMIN_ROLE"))
        db.session.add(admin_user)
        db.session.commit()

    # Register Blueprints
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_users)
    app.register_blueprint(bp_appointments)

    @app.get("/")
    def health():
        return "App is up and running!!", 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
