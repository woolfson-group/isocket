import itertools
import networkx
import numpy

from isocket_settings import global_settings
from isambard_dev.add_ons.filesystem import FileSystem
from isambard_dev.add_ons.knobs_into_holes import KnobGroup
from isambard_dev.ampal.pdb_parser import convert_pdb_to_ampal
from isambard_dev.add_ons.parmed_to_ampal import convert_cif_to_ampal
from isocket.graph_theory import graph_to_plain_graph, GraphHandler

data_dir = global_settings['structural_database']['path']


class StructureHandler:
    def __init__(self, assembly):
        self.assembly = assembly
        self.is_preferred = False
        self.code = self.assembly.id
        self.mmol = None

    @classmethod
    def from_code(cls, code, mmol=None):
        fs = FileSystem(code=code, data_dir=data_dir)
        if mmol is None:
            mmol = fs.preferred_mmol
        if mmol > fs.number_of_mmols:
            mmol = None
        preferred = True if mmol == fs.preferred_mmol else False
        # Try with cif file, if that fails try with pdb file.
        cif = fs.cifs[mmol]
        try:
            a = convert_cif_to_ampal(cif, assembly_id=code)
        except ValueError:
            pdb = fs.mmols[mmol]
            a = convert_pdb_to_ampal(pdb=pdb, path=True, pdb_id=code)
        instance = cls(assembly=a)
        instance.is_preferred = preferred
        instance.mmol = mmol
        instance.code = code
        return instance

    @classmethod
    def from_file(cls, filename, path=True, code='', cif=False):
        if cif:
            a = convert_cif_to_ampal(cif=filename, path=path)
            a.id = code
        else:
            a = convert_pdb_to_ampal(pdb=filename, path=path, pdb_id=code)
        instance = cls(assembly=a)
        return instance

    def get_knob_group(self, cutoff=10.0, state_selection=0):
        # try / except is for AmpalContainers
        try:
            knob_group = KnobGroup.from_helices(self.assembly, cutoff=cutoff)
        except AttributeError:
            knob_group = KnobGroup.from_helices(self.assembly[state_selection], cutoff=cutoff)
        return knob_group

    def get_knob_graphs(self, min_scut=7.0, max_scut=10.0, scut_increment=0.5):
        kg = self.get_knob_group(cutoff=max_scut)
        if kg is not None:
            scuts = list(numpy.arange(min_scut, max_scut + scut_increment, scut_increment))
            kcuts = list(range(4))
            g = kg.graph
            knob_graphs = []
            for scut, kcut in itertools.product(scuts[::-1], kcuts):
                h = kg.filter_graph(g=g, cutoff=scut, min_kihs=kcut)
                h = graph_to_plain_graph(g=h)
                # if is null graph
                if h.number_of_nodes() == 0:
                    continue
                if networkx.connected.is_connected(h):
                    ccs = [h]
                else:
                    ccs = sorted(networkx.connected_component_subgraphs(h, copy=True),
                                 key=lambda x: len(x.nodes()), reverse=True)
                for cc_num, cc in enumerate(ccs):
                    cc.graph.update(cc_num=cc_num, scut=scut, kcut=kcut)
                    knob_graphs.append(cc)
        else:
            knob_graphs = []
        return knob_graphs

    def get_atlas_graphs(self, mode='production'):
        knob_graphs = self.get_knob_graphs()
        atlas_graphs = []
        for g in knob_graphs:
            gh = GraphHandler(g, mode=mode)
            d = dict(scut=g.graph['scut'], kcut=g.graph['kcut'], code=self.code,
                     mmol=self.mmol, cc_num=g.graph['cc_num'], preferred=self.is_preferred,
                     nodes=g.number_of_nodes(), edges=g.number_of_edges())
            gh.g.graph.update(d)
            atlas_graphs.append(gh.g)
        return atlas_graphs
