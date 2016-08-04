import os

WTF_CSRF_ENABLED = True
DEBUG = False

basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
STATIC_FOLDER = os.path.join(basedir, 'app', 'static')
TEMP_FOLDER = os.path.join(basedir, 'tmp')
ALLOWED_EXTENSIONS = {'pdb', 'mmol', 'cif'}
