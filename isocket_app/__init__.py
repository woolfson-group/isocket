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

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
migrate = Migrate(app=app, db=db)

from isocket_app import views, models, populate_models
from .util import assets