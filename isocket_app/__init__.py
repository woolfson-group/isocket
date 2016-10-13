from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_app(config_filename=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py')
    if config_filename is not None:
        app.config.from_pyfile(config_filename)
    from isocket_app.models import db
    db.init_app(app)
    migrate = Migrate(app=app, db=db)
    return app

from isocket_app import views, models, populate_models
from .util import assets