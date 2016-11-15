import os
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True
    SECRET_KEY = 'change_this_key'
    # sqlite :memory: identifier is the default if no filepath is present
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    # Uploads folders for flask-uploads
    STATIC_FOLDER = os.path.join(basedir, 'isocket', 'static')
    UPLOADS_DEFAULT_DEST = os.path.join(STATIC_FOLDER, 'uploads')
    UPLOADED_STRUCTURES_DEST = os.path.join(UPLOADS_DEFAULT_DEST, 'structures')
    TEMP_FOLDER = os.path.join(basedir, 'tmp')
    UPLOADED_STRUCTURES_ALLOW = ('pdb', 'mmol', 'cif', 'mmcif')
    ASSETS_DEBUG = DEBUG


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:////Users/jackheal/Projects/isocket/isocket/atlas.db'


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../unit_tests/tests.db'


config = {
    "development": "config.DevelopmentConfig",
    "testing": "config.TestingConfig",
    "default": "config.DevelopmentConfig"
}


def configure_app(app):
    # get env variable ISOCKET_CONFIG, if doesn't exist, set to 'default'
    config_name = os.getenv(key='ISOCKET_CONFIG', default='default')
    app.config.from_object(config[config_name])
    app.config.from_pyfile('config.cfg', silent=True)


