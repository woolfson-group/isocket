from flask import Blueprint

structure_bp = Blueprint(
    'structure_bp',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/{}'.format(__name__)
)

from isocket.structure import views
