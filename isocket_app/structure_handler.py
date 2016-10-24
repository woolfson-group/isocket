import itertools
from collections import namedtuple

from isambard_dev.add_ons.filesystem import FileSystem
from isambard_dev.add_ons.knobs_into_holes import KnobGroup
from isambard_dev.add_ons.parmed_to_ampal import convert_cif_to_ampal
from isocket_app.graph_theory import graph_to_plain_graph, sorted_connected_components








def get_structure_data(code, preferred=True, mmol=1, cutoff=10.0):
    Structure = namedtuple('Structure', ['code', 'mmol', 'preferred', 'knob_group'])
    fs = FileSystem(code=code)
    if preferred:
        mmol = fs.preferred_mmol
    cif = fs.cifs[mmol]
    a = convert_cif_to_ampal(cif, assembly_id=code)
    kg = KnobGroup.from_helices(a, cutoff=cutoff)
    return Structure(code=code, mmol=mmol, preferred=preferred, knob_group=kg)


def get_graphs_from_knob_group(knob_group):
    scuts = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
    kcuts = list(range(4))
    g = knob_group.graph
    knob_graphs = []
    for scut, kcut in itertools.product(scuts[::-1], kcuts):
        h = knob_group.filter_graph(g=g, cutoff=scut, min_kihs=kcut)
        h = graph_to_plain_graph(g=h)
        ccs = sorted_connected_components(h)
        for cc_num, cc in enumerate(ccs):
            cc.graph.update(cc_num=cc_num, scut=scut, kcut=kcut)
            knob_graphs.append(cc)
    return knob_graphs