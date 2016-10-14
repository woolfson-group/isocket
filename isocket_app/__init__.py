from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


from isocket_app.home import views
from isocket_app.atlas import views
from isocket_app.structure import views
from isocket_app import models, populate_models
from .util import assets