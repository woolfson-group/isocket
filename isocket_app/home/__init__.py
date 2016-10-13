from flask import Blueprint

home = Blueprint(
    'home',
    __name__,
    template_folder='templates',
    static_folder='static'
)

from isocket_app.home import views
