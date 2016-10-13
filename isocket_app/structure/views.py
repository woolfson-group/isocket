import json
import os
import networkx
from flask import render_template, flash, redirect, request, url_for, current_app, Blueprint
from flask_uploads import UploadSet
from isambard_dev.add_ons.knobs_into_holes import KnobGroup
from isambard_dev.ampal.pdb_parser import convert_pdb_to_ampal
from networkx.readwrite import json_graph
from werkzeug.utils import secure_filename

from isocket_app.structure.forms import SocketForm
from isocket_app.structure import structure_bp


@structure_bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    structures = UploadSet(name='structures', extensions=current_app.config['UPLOADED_STRUCTURES_ALLOW'])
    form = SocketForm()
    if form.validate_on_submit():
        if 'structure' not in request.files:
            flash('Please upload a structure file.')
            return redirect(request.url)
        structure = request.files['structure']
        filename = secure_filename(structures.save(structure))
        return redirect(url_for('structure_bp.uploaded_file', filename=filename, scut=form.scut.data, kcut=form.kcut.data))
    return render_template('upload.html', form=form)


#TODO add tokens to urls to avoid problems with same url and different data
# (e.g. same filename with differnet file content).
@structure_bp.route('/uploads/pdb=<filename>_socket_cutoff=<scut>_knob_cutoff=<kcut>')
def uploaded_file(filename, scut, kcut):
    scut = float(scut)
    kcut = int(kcut)
    uploaded_structures_dest = current_app.config['UPLOADED_STRUCTURES_DEST']
    static_file_path = os.path.join(uploaded_structures_dest, filename)
    a = convert_pdb_to_ampal(static_file_path, path=True)
    kg = KnobGroup.from_helices(a, cutoff=scut)
    g = kg.filter_graph(kg.graph, cutoff=scut, min_kihs=kcut)
    h = networkx.Graph()
    h.add_nodes_from([x.number for x in g.nodes()])
    h.add_edges_from([(e[0].number, e[1].number) for e in g.edges()])
    graph_as_json = json_graph.node_link_data(h)
    graph_as_json = json.dumps(graph_as_json)
    return render_template('structure.html', structure=static_file_path, title=filename, kg=kg,
                           graph_as_json=graph_as_json)
