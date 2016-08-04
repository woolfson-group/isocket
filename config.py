import os

WTF_CSRF_ENABLED = True
DEBUG = False

basedir = os.path.abspath(os.path.dirname(__file__))

STATIC_FOLDER = os.path.join(basedir, 'app', 'static')
UPLOADS_DEFAULT_DEST = os.path.join(STATIC_FOLDER, 'uploads')
UPLOADED_STRUCTURES_DEST = os.path.join(UPLOADS_DEFAULT_DEST, 'structures')
TEMP_FOLDER = os.path.join(basedir, 'tmp')
UPLOADED_STRUCTURES_ALLOW = ('pdb', 'mmol', 'cif', 'mmcif')
