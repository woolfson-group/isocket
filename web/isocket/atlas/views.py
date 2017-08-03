from bokeh.embed import autoload_server
from flask import render_template

from isocket.atlas import atlas_bp


@atlas_bp.route('/app')
def atlas():
    script = autoload_server(
        model=None, url='http://coiledcoils.chm.bris.ac.uk/bokeh/atlas')
    return render_template('atlas.html', title='AtlasCC', bokeh_script=script)

