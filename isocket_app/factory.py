from flask import Flask
from flask_uploads import UploadSet, configure_uploads
from config import configure_app


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    configure_app(app=app)
    if config is not None:
        app.config.from_pyfile(config)
    # Database set up
    from isocket_app.extensions import db
    db.init_app(app)
    from isocket_app.extensions import assets
    assets.init_app(app)
    from isocket_app.extensions import migrate
    migrate.init_app(app, db)
    # Register Blueprints
    from isocket_app.home import home_bp
    app.register_blueprint(home_bp)
    from isocket_app.atlas import atlas_bp
    app.register_blueprint(atlas_bp)
    from isocket_app.structure import structure_bp
    app.register_blueprint(structure_bp)
    # Flask-assets, flask-uploads
    from isocket_app.util.assets import bundles
    assets.register(bundles)
    structures = UploadSet(name='structures', extensions=app.config['UPLOADED_STRUCTURES_ALLOW'])
    configure_uploads(app, structures)
    return app

