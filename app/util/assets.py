from flask_assets import Bundle, Environment
from .. import app

bundles = {
    'structure_js': Bundle(
        'js/lib/bio-pv.min.js',
        'js/lib/pv_custom.js',
        'js/lib/d3.js',
        'js/graph_drawing.js',
        output='gen/structure.js'
    )
}

assets = Environment(app)
assets.register(bundles)
