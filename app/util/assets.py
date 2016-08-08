from flask_assets import Bundle, Environment
from .. import app

bundles = {
    'structure_js': Bundle(
        'js/graph_drawing.js',
        'js/lib/bio-pv.min.js',
        'js/lib/pv_custom.js',
        output='gen/structure.js',
        filters='jsmin'
    ),

    'base_js': Bundle(
        'js/lib/jquery-3.1.0.min.js',
        'js/lib/bootstrap.min.js',
        output='gen/base.js',
        filters='jsmin'
    ),

    'base_css': Bundle(
        'css/lib/bootstrap.min.css',
        'css/lib/bootstrap-responsive.min.css',
        output='gen/base.css',
        filters='cssmin'
    )
}

assets = Environment(app)
assets.register(bundles)
