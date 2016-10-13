from flask import Blueprint

home = Blueprint(
    'home',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/{}'.format(__name__)
)

from isocket_app.home import views
