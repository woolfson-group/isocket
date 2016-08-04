import os
from isambard.add_ons.knobs_into_holes import KnobGroup
from isambard.ampal.pdb_parser import convert_pdb_to_ampal
from flask import render_template, flash, redirect, request, url_for, send_from_directory, render_template_string
from app import app
from .forms import LoginForm, SocketForm
from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, TEMP_FOLDER, STATIC_FOLDER
from werkzeug.utils import secure_filename
import networkx
from networkx.readwrite import json_graph
import tempfile
import json

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='iSOCKET')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    form = SocketForm()
    if request.method == 'POST':
    #if form.validate_on_submit():
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            #file.save(os.path.join(UPLOAD_FOLDER, filename))
            request.view_args['blah'] = 5
            return redirect(url_for('uploaded_file', filename=filename, scut=form.scut.data, kcut=form.kcut.data))

    return render_template('upload.html', form=form)


#TODO add tokens to urls to avoid problems with same url and different data
# (e.g. same filename with differnet file content).
@app.route('/uploads/pdb=<filename>_socket_cutoff=<scut>_knob_cutoff=<kcut>')
def uploaded_file(filename, scut, kcut):
    file = os.path.join(STATIC_FOLDER, filename)
    a = convert_pdb_to_ampal(file, path=True)
    kg = KnobGroup.from_helices(a, cutoff=scut)
    g = kg.graph
    h = networkx.Graph()
    h.add_nodes_from([x.number for x in g.nodes()])
    h.add_edges_from([(e[0].number, e[1].number) for e in g.edges()])
    graph_as_json = json_graph.node_link_data(h)
    graph_as_json = json.dumps(graph_as_json)
    print(graph_as_json)
    return render_template('structure.html', title=filename, kg=kg, graph_as_json=graph_as_json)

