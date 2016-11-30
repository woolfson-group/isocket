import pandas
import numpy
import networkx as nx
import os
from networkx.generators.atlas import graph_atlas_g
from collections import OrderedDict
from bokeh.plotting import Figure, curdoc
from bokeh.palettes import Reds9
from bokeh.layouts import WidgetBox
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.models import Slider, HBox, Select

from isocket_settings import global_settings
from isocket.graph_theory import AtlasHandler

filename = os.path.join(global_settings['package_path'], 'isocket', 'data', '2016-11-29_graph_names.h5')


def points_on_a_circle(n, radius=1, centre=(0, 0), rotation=0):
    """ List of uniformly distributed (x, y) coordinates on the circumference of a circle.

    Parameters
    ----------
    n : int
        Number of points to return.
    radius : float
    centre : tuple or list or numpy.array
    rotation : float
        Angle in degrees by which all points will be rotated.
        rotation = 0 means that the line from the centre to the first point is parallel to the x-axis.
        rotation > 0 => anti-clockwise rotation

    Returns
    -------
    points : list(2-tuples)
        (x, y) coordinates of uniformly distributed points on the circumference of the circle
    """
    rotation = numpy.deg2rad(rotation)
    thetas = [numpy.divide(i * numpy.pi * 2, n) + rotation for i in range(n)]
    points = [(radius * numpy.cos(theta) + centre[0], radius * numpy.sin(theta) + centre[1]) for theta in thetas]
    return points


# Get graphs and format plot accordingly
def get_graph_array(atlas=True, cyclics=True, unknowns=False, paths=False, max_nodes=8):
    gag = AtlasHandler().get_graph_list(atlas=atlas, cyclics=cyclics,
                                        unknowns=unknowns, paths=paths,
                                        max_cyclics=max_nodes, max_paths=max_nodes)
    gag = [g for g in gag if g.number_of_nodes() >= 2]
    gag = [g for g in gag if g.number_of_nodes() <= max_nodes]
    gag = [g for g in gag if nx.connected.is_connected(g) and max(g.degree().values()) <= 4]
    nrows = int(numpy.floor(numpy.sqrt(len(gag))))
    ncols = int(numpy.ceil(len(gag)/float(nrows)))
    size_diff = nrows*ncols - len(gag)
    # Fill in square array with None
    sq_gag = gag + [None]*size_diff
    sq_gag = numpy.reshape(sq_gag, (ncols, nrows))
    return sq_gag

max_nodes = 8
sq_gag = get_graph_array(max_nodes=max_nodes)

tools = "pan,wheel_zoom,box_zoom,reset,resize"
# Define the figure.
p = Figure(
    plot_height=1000,
    plot_width=1000,
    webgl=True,
    x_range=(-1, sq_gag.shape[0]),
    y_range=(sq_gag.shape[1], -1),
    tools=tools,
)
p.grid.grid_line_color = None
p.axis.visible = False
p.title.text = "AtlasCC: An Atlas of Coiled Coils"
p.toolbar.logo = None
p.outline_line_width = 5
p.outline_line_color = "Black"

#
#max_nodes = max([g.number_of_nodes() for g in gag])
circles = {n: points_on_a_circle(n=n, radius=0.4) for n in range(1, max_nodes + 1)}
all_circles = []
all_xs = []
all_ys = []
all_gnames = []
for i, g in numpy.ndenumerate(sq_gag):
    if g:
        all_gnames.append(g.name)
        xs = []
        ys = []
        c = circles[g.number_of_nodes()] + numpy.array(i)
        all_circles.append(c)
        try:
            for e1, e2 in g.edges_iter():
                xs.append([c[e1][0], c[e2][0]])
                ys.append([c[e1][1], c[e2][1]])
        except IndexError:
            print(g.name)
        all_xs += xs
        all_ys += ys
circle_xys = numpy.concatenate(all_circles)
p.circle(x=circle_xys[:,0], y=circle_xys[:,1], radius=0.02)
p.multi_line(xs=all_xs, ys=all_ys)


df = pandas.read_hdf(filename, 'graph_names')

scut = Slider(
    title="scut", name='scut',
    value=7.0, start=7.0, end=9.0, step=0.5
)

kcut = Slider(
    title="kcut", name='kcut',
    value=2, start=0, end=3, step=1)


inputs = WidgetBox(
    children=[
        scut, kcut
    ]
)
hbox = HBox(children=[inputs, p])

# Use the above lists to populate a ColumnDataSource object with details needed for the hover labels.
source = ColumnDataSource(
    data=dict(
            gnames=[],
            r_colors=[],
            r_xs=[],
            r_ys=[],
            rel_freqs=[],
            counts=[],
            percents=[]
    )
)


def update_data():
    """Called each time that any watched property changes.
        This updates the sin wave data with the most recent values of the
        sliders. This is stored as two numpy arrays in a dict into the app's
        data source property.
        """
    # Get the current slider values
    s = scut.value
    k = kcut.value
    filtered_df = df[(df['scut'] == s) & (df['kcut'] == k)]
    '''
    r = redundancy.value
    if r != "No filter":
        rstring = "c{0}".format(r)
        pdbs = cddf[cddf[rstring] == True].pdb.values
        filtered_df = filtered_df[filtered_df['pdb'].isin(pdbs)]
    '''
    gb = filtered_df.groupby(df['gname'])
    rgs = gb.count().gname
    # From the graph counts, get the lists of rectangle positions and frequencies for the hover labels.
    total_graphs = sum(rgs.values)
    rel_freqs = []
    r_xs = []
    r_ys = []
    r_colors = []
    gnames = []
    counts = []
    cm = [x for x in reversed(Reds9)]
    for i, g in numpy.ndenumerate(sq_gag):
        if g:
            if g.name in rgs.index:
                counts.append(rgs[g.name])
                rel_freq = numpy.divide(float(rgs[g.name]), total_graphs)
                rel_freqs.append(rel_freq)
                r_xs.append(i[0])
                r_ys.append(i[1])
                gnames.append(g.name)
                color_index = min(len(cm) - 1, int(numpy.ceil(rel_freq * 10)))
                r_colors.append(cm[color_index])

    percents = ['{0:.2f}'.format(x * 100) for x in rel_freqs]

    data = dict(
        gnames=gnames,
        r_colors=r_colors,
        r_xs=r_xs,
        r_ys=r_ys,
        rel_freqs=rel_freqs,
        counts=counts,
        percents=percents
    )

    source.data = data

update_data()

# Configure hover tool and add the rectangles with the hover tool set up.
p.add_tools(HoverTool())
hover = p.select(dict(type=HoverTool))
hover.tooltips = OrderedDict([
    ('Graph Name', "@gnames"),
    ('Count', '@counts'),
    ('Percentage', '@percents')
])
p.rect(x='r_xs', y='r_ys', width=1, height=1,
       width_units="data", height_units="data",
       color='r_colors', alpha=0.5, source=source)


def input_change(attrname, old, new):
    """Executes whenever the input form changes.
    It is responsible for updating the plot, or anything else you want.
    Args:
        attrname : the attr that changed
        old : old value of attr
        new : new value of attr
        """
    update_data()


for w in [scut, kcut]:
    w.on_change('value', input_change)

curdoc().add_root(hbox)
#session = push_session(curdoc())
#script = autoload_server(p, session_id=session.id)
