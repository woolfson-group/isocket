from flask import Blueprint

atlas_bp = Blueprint(
    'atlas_bp',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/{}'.format(__name__)
)

from isocket_app.atlas import views
