import os
from isambard.add_ons.knobs_into_holes import KnobGroup
from isambard.ampal.pdb_parser import convert_pdb_to_ampal
from flask import render_template, flash, redirect, request, url_for
from app import app
from .forms import SocketForm
from flask_uploads import UploadSet, configure_uploads
from config import STATIC_FOLDER, UPLOADED_STRUCTURES_ALLOW, UPLOADED_STRUCTURES_DEST
from werkzeug.utils import secure_filename
import networkx
from networkx.readwrite import json_graph
import json

structures = UploadSet(name='structures', extensions=UPLOADED_STRUCTURES_ALLOW)
configure_uploads(app, structures)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='iSOCKET')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    form = SocketForm()
    if form.validate_on_submit():
        if 'structure' not in request.files:
            flash('Please upload a structure file.')
            return redirect(request.url)
        structure = request.files['structure']
        filename = secure_filename(structures.save(structure))
        return redirect(url_for('uploaded_file', filename=filename, scut=form.scut.data, kcut=form.kcut.data))
    return render_template('upload.html', form=form)


#TODO add tokens to urls to avoid problems with same url and different data
# (e.g. same filename with differnet file content).
@app.route('/uploads/pdb=<filename>_socket_cutoff=<scut>_knob_cutoff=<kcut>')
def uploaded_file(filename, scut, kcut):
    file = os.path.join(UPLOADED_STRUCTURES_DEST, filename)
    a = convert_pdb_to_ampal(file, path=True)
    kg = KnobGroup.from_helices(a, cutoff=scut)
    g = kg.graph
    h = networkx.Graph()
    h.add_nodes_from([x.number for x in g.nodes()])
    h.add_edges_from([(e[0].number, e[1].number) for e in g.edges()])
    graph_as_json = json_graph.node_link_data(h)
    graph_as_json = json.dumps(graph_as_json)

    print(file)
    return render_template('structure.html', structure=file, title=filename, kg=kg, graph_as_json=graph_as_json)

