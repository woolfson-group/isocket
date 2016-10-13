from flask import render_template
from bokeh.embed import autoload_server
from isocket_app.atlas import atlas_bp


@atlas_bp.route('/atlas')
def atlas():
    script = autoload_server(model=None, app_path='/atlas')
    return render_template('atlas.html', title='AtlasCC', bokeh_script=script)

