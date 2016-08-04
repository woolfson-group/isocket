from flask_assets import Bundle, Environment
from .. import app

bundles = {
    'structure_js': Bundle(
        'js/graph_drawing.js',
        'js/lib/bio-pv.min.js',
        'js/lib/pv_custom.js',
        output='gen/structure.js',
        filters='jsmin'
    )
}

assets = Environment(app)
assets.register(bundles)
