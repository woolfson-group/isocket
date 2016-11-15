from flask_sqlalchemy import SQLAlchemy
from flask_assets import Environment
from flask_migrate import Migrate

db = SQLAlchemy()
assets = Environment()
migrate = Migrate()