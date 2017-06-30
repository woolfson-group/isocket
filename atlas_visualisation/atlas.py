import pandas
import numpy
import os
import pickle
from collections import OrderedDict
from bokeh.plotting import Figure, curdoc
from bokeh.palettes import viridis
from bokeh.layouts import WidgetBox
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.models import Slider, HBox, Select
from bokeh.models.ranges import Range1d

data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
filename = os.path.join(data_folder, 'atlas.h5')
with open(os.path.join(data_folder, 'ccplus_codes.p'), 'rb') as foo:
    cc_plus_codes = pickle.load(foo)
df = pandas.read_hdf(filename, 'graph_names')
_color_map = viridis(34)


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


def graph_list_to_array(graph_list, nrows=None, ncols=None):
    ngraphs = len(graph_list)
    if (nrows is None) and (ncols is None):
        nrows = int(numpy.floor(numpy.sqrt(len(graph_list))))
        ncols = int(numpy.ceil(len(graph_list) / float(nrows)))
    elif nrows is None:
        if ngraphs % ncols == 0:
            nrows = ngraphs / ncols
        else:
            nrows = int(numpy.floor(ngraphs / ncols )) + 1
    elif ncols is None:
        if ngraphs % nrows == 0:
            ncols = ngraphs / nrows
        else:
            ncols = int(numpy.floor(ngraphs / nrows)) + 1
    size_diff = nrows * ncols - len(graph_list)
    if size_diff < 0:
        # defaults to square array
        nrows = int(numpy.floor(numpy.sqrt(len(graph_list))))
        ncols = int(numpy.ceil(len(graph_list) / float(nrows)))
    # Fill in square array with None
    graph_array = graph_list + [None] * size_diff
    graph_array = numpy.reshape(graph_array, (ncols, nrows))
    return graph_array


graph_list_pickle = os.path.join(data_folder, 'graph_list.p')
with open(graph_list_pickle, 'rb') as foo:
    graph_list  = pickle.load(foo)
max_nodes = max([g.number_of_nodes() for g in graph_list])
graph_array = graph_list_to_array(graph_list=graph_list)


def get_base_figure():
    tools = "pan,wheel_zoom,box_zoom,reset,resize"
    # Define the figure.
    p = Figure(
        plot_height=1000,
        plot_width=1000,
        webgl=True,
        tools=tools,
    )
    p.grid.grid_line_color = None
    p.axis.visible = False
    p.title.text = "AtlasCC: An Atlas of Coiled Coils"
    p.toolbar.logo = None
    p.outline_line_width = 5
    p.outline_line_color = "Black"
    return p


def add_graph_glyphs():
    p.x_range = Range1d(-1, graph_array.shape[0])
    p.y_range = Range1d(graph_array.shape[1], -1)
    circles = {n: points_on_a_circle(n=n, radius=0.4) for n in range(1, max_nodes + 1)}
    all_circles = []
    all_xs = []
    all_ys = []
    for i, g in numpy.ndenumerate(graph_array):
        if g:
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
    p.circle(x=circle_xys[:, 0], y=circle_xys[:, 1], radius=0.02)
    p.multi_line(xs=all_xs, ys=all_ys)
    return


p = get_base_figure()
add_graph_glyphs()



scut = Slider(
    title="scut", name='scut',
    value=7.0, start=7.0, end=9.0, step=0.5
)

kcut = Slider(
    title="kcut", name='kcut',
    value=2, start=0, end=3, step=1)

min_count = Slider(
    title="Minimum count", name='min_count',
    value=10, start=1, end=50, step=1)

code_select = Select(title="PDB codes:", value="CC+", options=["CC+", "All"])

inputs = WidgetBox(
    children=[
        scut, kcut, min_count, code_select
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


def get_box_color(count):
    cm = _color_map
    if count <= 20:
        c = count
    elif count <= 30:
        c = 21
    elif count <= 40:
        c = 22
    elif count <= 50:
        c = 23
    elif count <= 60:
        c = 24
    elif count <= 70:
        c = 25
    elif count <= 80:
        c = 26
    elif count <= 90:
        c = 27
    elif count <= 100:
        c = 28
    elif count <= 150:
        c = 29
    elif count <= 200:
        c = 30
    elif count <= 300:
        c = 31
    elif count <= 500:
        c = 32
    else:
        c = 33
    return cm[len(cm) - c]


def update_data():
    """Called each time that any watched property changes.
        This updates the sin wave data with the most recent values of the
        sliders. This is stored as two numpy arrays in a dict into the app's
        data source property.
        """
    # Get the current slider values
    s = scut.value
    k = kcut.value
    mc = min_count.value
    codes = code_select.value
    filtered_df = df[(df['scut'] == s) & (df['kcut'] == k)]
    if codes == 'CC+':
        filtered_df = filtered_df[filtered_df.pdb.isin(cc_plus_codes)]
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
    alphas = []
    for i, g in numpy.ndenumerate(graph_array):
        if g:
            if g.name in rgs.index:
                count = rgs[g.name]
                rel_freq = numpy.divide(float(rgs[g.name]), total_graphs)
                rel_freqs.append(rel_freq)
                r_colors.append(get_box_color(count=count))
            else:
                count = 0
                rel_freqs.append(0)
                r_colors.append('#ffffff') #white
            counts.append(count)
            r_xs.append(i[0])
            r_ys.append(i[1])
            gnames.append(g.name)
            if count >= mc:
                alphas.append(0.5)
            else:
                alphas.append(0.0)
    percents = ['{0:.2f}'.format(x * 100) for x in rel_freqs]

    data = dict(
        gnames=gnames,
        r_colors=r_colors,
        r_xs=r_xs,
        r_ys=r_ys,
        rel_freqs=rel_freqs,
        counts=counts,
        percents=percents,
        alphas=alphas
    )

    source.data = data

update_data()

# Configure hover tool and add the rectangles with the hover tool set up.
boxes = p.rect(x='r_xs', y='r_ys',
               width=1, height=1, width_units="data", height_units="data",
               color='r_colors', alpha='alphas', source=source)
hover = HoverTool(renderers=[boxes],
                  tooltips=OrderedDict([('Graph Name', "@gnames"),
                                        ('Count', '@counts'),
                                        ('Percentage', '@percents')])
                  )
p.add_tools(hover)


def input_change(attrname, old, new):
    """Executes whenever the input form changes.
    It is responsible for updating the plot, or anything else you want.
    Args:
        attrname : the attr that changed
        old : old value of attr
        new : new value of attr
        """
    update_data()


for w in [scut, kcut, min_count, code_select]:
    w.on_change('value', input_change)

curdoc().add_root(hbox)

