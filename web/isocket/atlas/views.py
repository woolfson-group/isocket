from bokeh.embed import autoload_server
from flask import render_template

from web.isocket.atlas import atlas_bp


@atlas_bp.route('/atlas')
def atlas():
    script = autoload_server(model=None, url='http://localhost:5006/atlas')
    return render_template('atlas.html', title='AtlasCC', bokeh_script=script)

