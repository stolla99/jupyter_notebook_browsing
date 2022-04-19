import copy
import os
import ast
import itertools
import subprocess
import time

import pygraphviz as pgv
from typing import Callable
from nbformat import read, NO_CONVERT
from data_tracing.extract_cfg import ControlFlowExtractor
from data_tracing.extract_dfg import DataFlowExtractor
from alive_progress import alive_bar

type_check_ld_st: Callable[[ast.AST], bool] = lambda arg: not (isinstance(arg, ast.Load) or isinstance(arg, ast.Store)
                                                               or isinstance(arg, ast.operator)
                                                               or isinstance(arg, ast.unaryop))


def node_str_generator(ast_node, current_cell):
    """

    :param current_cell: Current cell resulting from the notebook.
    :param ast_node: Node from the ast which has all the information to create a label for the graph

    :return: name for the node in the graph and dictionary with attributes
    """
    if isinstance(ast_node, str):
        return ast_node, {}
    cell_str = "$cell" + str(current_cell)
    attribute_dict = dict()
    attribute_dict["margin"] = "0.1"
    if isinstance(ast_node, ast.Module):
        label = ""
        attribute_dict["label"] = label
        attribute_dict["shape"] = "underline"
    elif isinstance(ast_node, ast.For):
        temp = copy.deepcopy(ast_node)
        temp.body.clear()
        label = ast.unparse(temp)
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.FunctionDef):
        attributes = ast_node.__dict__
        label = "FunctionDef\\n"
        name = attributes['name']
        attribute_dict["label"] = label + name
    elif isinstance(ast_node, ast.Name):
        attributes = ast_node.__dict__
        label = attributes['id']
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.Assign):
        code_line = ast.unparse(ast_node)
        code_line_split = code_line.split("=")
        label = "=" + code_line_split[0]
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.Import) or isinstance(ast_node, ast.ImportFrom) \
            or isinstance(ast_node, ast.Expr):
        code_line = ast.unparse(ast_node)
        label = code_line
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.Call):
        code_line = ast.unparse(ast_node)
        label = code_line
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.Constant):
        attributes = ast_node.__dict__
        value = attributes['value']
        label = "\'" + str(value) + "\'"
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.Attribute):
        code_line = ast.unparse(ast_node)
        label = code_line
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.Dict):
        code_line = ast.unparse(ast_node)
        code_line.replace("{", 'U+007B')
        label = code_line
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.arg):
        attributes = ast_node.__dict__
        arg = attributes['arg']
        label = "arg\\n" + str(arg)
        attribute_dict["label"] = label
    else:
        code_line = ast.unparse(ast_node)
        label = code_line
        attribute_dict["label"] = label
    return label + str(ast_node) + cell_str, attribute_dict


def node_traversal(nd, current_cell):
    """
    Function traverses the ast of the code beginning from the module node of the ast. Each ast corresponds
    to a code cell in the jupyter notebook file.

    :param current_cell: Cell in which the ast is traversed, cell from the notebook
    :param nd: current node in the ast
    """
    skip_edge_list = False

    node_str, attribute_dict = node_str_generator(nd, current_cell)
    if not (node_str in node_list) and type_check_ld_st(nd):
        node_list.append((node_str, attribute_dict))
    if isinstance(nd, ast.AST):
        if isinstance(nd, ast.FunctionDef):
            skip_edge_list = True
        lst = ast.iter_fields(nd)
        for field, value in lst:
            # Delete forward edges from function_def, so in other words skip body of function node.
            if skip_edge_list and field == "body":
                # In case we have a ast.FunctionDef and the field is body we skip the edges.
                if isinstance(value, list):
                    for child in value:
                        if isinstance(child, ast.AST) and type_check_ld_st(child):
                            node_traversal(child, current_cell)
                elif isinstance(value, ast.AST) and type_check_ld_st(value):
                    node_traversal(value, current_cell)
            else:
                # Insert every edge in the edge list as normal into the AST
                if isinstance(value, list):
                    for child in value:
                        if isinstance(child, ast.AST) and type_check_ld_st(child):
                            edge_list.append((node_str, node_str_generator(child, current_cell)[0]))
                            node_traversal(child, current_cell)
                elif isinstance(value, ast.AST) and type_check_ld_st(value):
                    edge_list.append((node_str, node_str_generator(value, current_cell)[0]))
                    node_traversal(value, current_cell)


def trim_string(node_str):
    """

    :param node_str:
    :return:
    """
    return str(int.from_bytes(node_str.encode(), 'little'))


def prepare_html(s):
    """

    :param s:
    """
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    return s


def get_width_of_table(html_str):
    """
    Calculates the width of an HTML element by calling render_html.py

    :param html_str: Valid HTML code
    :return: offsetWidth of the rendered HTML element
    """
    p = subprocess.Popen(['python', 'render_html.py', html_str], stdout=subprocess.PIPE)
    width = int(p.stdout.readline().decode('utf-8'))
    p.wait()
    p.kill()
    return width


def process_node(node, cell_key):
    """

    :param node:
    :param cell_key:
    """
    dfg_ex = DataFlowExtractor(node)
    attr_node_dict = {"shape": "plaintext", "margin": "0.1"}
    if isinstance(node, ast.Assign):
        dfg_node_list = dfg_ex.walk_tree_by_name(no_dict=True, ast=node, cell_num=cell_key, to_exclude=node.targets)

        target_string = "<<TABLE WIDTH=\"\" BORDER=\"0\" CELLBORDER=\"1\" CELLSPACING=\"4\" CELLPADDING=\"4\">" \
                        + "<TR>" \
                        + "".join(["<TD ROWSPAN=\"2\" PORT=\"" + trim_string(node_str_generator(n, cell_key)[0])
                                   + "\">"
                                   + prepare_html((node_str_generator(n, cell_key)[1])["label"])
                                   + "</TD>"
                                   for n in node.targets]) \
                        + "<TD COLSPAN=\"" + str(max(1, len(dfg_node_list))) + "\">" \
                        + prepare_html((node_str_generator(node.value, cell_key)[1])["label"]) \
                        + "</TD>" \
                        + "</TR>"
        used_var_str = ""
        if len(dfg_node_list) > 0:
            used_var_str += "<TR>" + "".join(["<TD PORT=\""
                                              + trim_string(node_str_generator(n, int(val))[0])
                                              + "\">"
                                              + prepare_html((node_str_generator(n, int(val))[1])["label"])
                                              + "</TD>"
                                              for n, val in dfg_node_list]) + "</TR>"
        else:
            used_var_str += "<TR><TD></TD></TR>"

        label = target_string + used_var_str + "</TABLE>>"
        attr_node_dict["label"] = label
        return node_str_generator(node, cell_key)[0], attr_node_dict
    elif isinstance(node, ast.Expr):
        dfg_node_list = dfg_ex.walk_tree_by_name(no_dict=True, ast=node, cell_num=cell_key, to_exclude=[])
        label = prepare_html((node_str_generator(node, cell_key)[1])["label"])
        label = "<<TABLE WIDTH=\"\" BORDER=\"0\" CELLBORDER=\"1\" CELLSPACING=\"4\" CELLPADDING=\"4\">" \
                + "<TR><TD COLSPAN=\"" + str(max(1, len(dfg_node_list))) + "\">" + label + "</TD></TR>"
        if len(dfg_node_list) > 0:
            label += "<TR>" + "".join(["<TD PORT=\""
                                       + trim_string(node_str_generator(var, cell_key)[0])
                                       + "\">"
                                       + prepare_html(((node_str_generator(var, cell_num))[1])["label"])
                                       + "</TD>"
                                       for var, cell_num in dfg_node_list]) + "</TR></TABLE>>"
        else:
            label += "</TABLE>>"
        attr_node_dict["label"] = label
        return node_str_generator(node, cell_key)[0], attr_node_dict


# file = 'data_vis_exer_1'
file = 'comprehensive-data-exploration-with-python'
ext = '.ipynb'
path = '../notebooks/'
dir_list = os.listdir(path)
print(dir_list)
# TODO: Convert all

with open(path + file + ext) as fp:
    notebook = read(fp, NO_CONVERT)
cells = notebook['cells']
code_cells = [c for c in cells if c['cell_type'] == 'code']

# One ast (ready for the graph) for every code cell, contains (List of nodes, List of edges)
ast_dict = dict()
# Dictionary with the ASTs itself
ast_dict_parsed = dict()

# Node and edge lists
node_list = []
edge_list = []
# Module node for every cell or cluster
cluster_head_list = []

for cell, i in itertools.zip_longest(code_cells, range(len(code_cells))):
    source = cell['source']
    try:
        ast_cell = ast.parse(source=source)
        print(source)
    except SyntaxError:
        print('Parsing failed with SyntaxError')
        ast_cell = ast.parse(source='\n')
    # Save ast itself for the CFG extraction (and data flow)
    body = ast_cell.__dict__['body']
    if len(body) > 0:
        ast_dict_parsed[str(i)] = ast_cell
        node_traversal(ast_cell, i)
        ast_dict[str(i)] = (node_list.copy(), edge_list.copy())
        node_list.clear()
        edge_list.clear()

# Create graph from edge list and nodelist using the dot-layout
G = pgv.AGraph(strict=False,
               directed=True,
               label="ast_" + file,
               compound=True,
               rankdir="TB",
               splines="spline")
# Set some default attributes
G.node_attr['shape'] = 'plaintext'

# Dictionary with nodes of the cfg for every cell
cfg_dict = dict()
# Dictionary with the node of the control flow excluding ast.Module for the DataFlow
ast_cfg_nodes_dict = dict()

# Assign nodes to be processed later
assign_nodes = []

# Extract the flow graphs from the ASTs of every cell in the jupyter notebook (potentially)
cfg_ex = ControlFlowExtractor()

# List with all nodes
line_nodes = []

print()
with alive_bar(len(ast_dict_parsed.keys()),
               theme='smooth',
               stats=False,
               monitor="{count}/{total}",
               force_tty=True,
               title='Processing Cells') as bar:
    for cell_key in ast_dict_parsed.keys():
        ast_cell = ast_dict_parsed[cell_key]
        cfg_ex.extract_CFG(ast_cell)

        # Call this get_edge_list() before get.nodes() to include targets and values of ast.Assign
        edge_list = cfg_ex.get_edge_list()
        # Save for DataFlowExtractor later
        ast_cfg_nodes_dict[cell_key] = cfg_ex.get_nodes(skip_module=True)

        cluster_head = None
        # "nodes" has string and attribute dict as content
        nodes = []

        # html nodes
        html_nodes = []
        for node in cfg_ex.get_nodes():
            if isinstance(node, ast.Module):
                cluster_head = node
                nodes.append(node_str_generator(node, cell_key))
            elif isinstance(node, ast.Assign):
                html_nodes.append(process_node(node, cell_key))
            elif isinstance(node, ast.Expr):
                html_nodes.append(process_node(node, cell_key))
            else:
                nodes.append(node_str_generator(node, cell_key))

        # Create html_doc to render and obtain max offsetWidth to ensure left alignment of tables in nodes of the graph
        html_doc = ""
        for (node_str, attr_dict) in html_nodes:
            html_str = attr_dict["label"]
            html_doc += html_str[1:len(html_str) - 1]

        max_width = get_width_of_table(html_doc)
        # TODO: Loading
        for (node_str, attr_dict) in html_nodes:
            label = attr_dict["label"]
            attr_dict["label"] = label.replace("WIDTH=\"\"", "WIDTH=\"" + str(max_width) + "\"")
            nodes.append((node_str, attr_dict))
        html_nodes.clear()

        cfg_nodes_sorted = ast_cfg_nodes_dict[cell_key]
        cfg_nodes_sorted.sort(key=lambda elem: elem.__dict__["lineno"])
        previous_node_str = None
        first = True
        for node in cfg_nodes_sorted:
            label_ext = ""
            lineno = str(node.__dict__["lineno"])
            end_lineno = str(node.__dict__["end_lineno"])
            if lineno == end_lineno:
                label_ext += lineno
            else:
                label_ext += lineno + " - " + end_lineno
            node_str = node_str_generator(node, cell_key)[0] + "$line" + label_ext
            if first:
                line_nodes.append(node_str)
                first = False
            nodes.append((node_str,
                          {"label": "<<FONT COLOR=\"grey\" FACE=\"Monospace\"><B>Line</B> " + label_ext + ":" + "</FONT>>",
                           "shape": "plaintext"}))
            edge_list.append(((node_str, node), {"color": "grey", "constraint": "False", "arrowhead": "none"}))
            if previous_node_str is not None:
                edge_list.append(((previous_node_str, node_str),
                                  {"color": "grey",
                                   "arrowhead": "none",
                                   "weight": 3}))
            previous_node_str = node_str

        # Adding cluster anchor nodes with the corresponding cell number (node_str, cell_num)
        if cluster_head is not None:
            cluster_head_list.append((cluster_head, cell_key))
        else:
            raise ModuleNotFoundError
        cfg_dict[cell_key] = nodes

        for (node, attr_dict) in nodes:
            G.add_node(node, **attr_dict)

        G.add_subgraph(cfg_ex.get_nodes(), "cfg_cell" + str(cell_key))

        for ((x, y), attr) in edge_list:
            G.add_edge(node_str_generator(x, cell_key)[0], node_str_generator(y, cell_key)[0], **attr)
        # Update beautiful progress bar
        time.sleep(0)
        bar()

# Add cluster with name cluster[cell number] into the graph with name Cell_[cell number]
for cell_key in cfg_dict.keys():
    n_e_tuple = cfg_dict[cell_key]
    name = 'Cell ' + cell_key
    G.subgraph(list(map(lambda elem: elem[0], n_e_tuple)), name="cluster" + cell_key, label=name)

# Ensure that cells are displayed from left to right in the graph => Place Module node of every cell onto the same level
# cluster_head_list = [node_str_generator(node, cell)[0] for (node, cell) in cluster_head_list]
dummy_nodes = []
first = True
for x, y in itertools.pairwise(cluster_head_list):
    x_str = node_str_generator(x[0], x[1])[0]
    y_str = node_str_generator(y[0], y[1])[0]
    x_str_ext = x_str + "$line" + str(x[1])
    y_str_ext = y_str + "$line" + str(y[1])
    if first:
        dummy_nodes.append(x_str_ext)
        first = False
    dummy_nodes.append(y_str_ext)
    G.add_node(x_str_ext, label="dummy" + str(x[1]))
    G.add_node(y_str_ext, label="dummy" + str(y[1]))
    if not G.has_edge(x_str_ext, x_str):
        G.add_edge(x_str_ext, x_str)
    G.add_edge(x_str, y_str_ext)
    G.add_edge(y_str_ext, y_str)
#   G.add_edge(x, y, style="invis")

# Prepare the head list and extend with dummy nodes
temp = [node_str_generator(node, cell)[0] for (node, cell) in cluster_head_list]
temp.extend(dummy_nodes)
G.add_subgraph(temp, rank="same")

assert len(dummy_nodes) == len(line_nodes)
for dummy, line in itertools.zip_longest(dummy_nodes, line_nodes):
    G.add_edge(dummy, line, weight=2)

dfg_ex = DataFlowExtractor(ast_dict_parsed)
attr = {"color": "#fc0303"}
dfg_edge_list = dfg_ex.walk_and_get_edges()
for n_v_tupleU, n_v_tupleV in dfg_edge_list:
    parent_U = dfg_ex.get_parent_node(n_v_tupleU[0], ast_cfg_nodes_dict[n_v_tupleU[1]])
    parent_V = dfg_ex.get_parent_node(n_v_tupleV[0], ast_cfg_nodes_dict[n_v_tupleV[1]])
    if parent_V is None or parent_U is None:
        # TODO eval function def edges
        continue
    elif parent_U == parent_V:
        continue
    else:
        nameU, _ = node_str_generator(n_v_tupleU[0], n_v_tupleU[1])
        nameV, _ = node_str_generator(n_v_tupleV[0], n_v_tupleV[1])
        G.add_edge(node_str_generator(parent_U, n_v_tupleU[1])[0],
                   node_str_generator(parent_V, n_v_tupleV[1])[0],
                   tailport=trim_string(nameU) + ":" + "s",
                   headport=trim_string(nameV) + ":" + "n",
                   **attr)

# Layout chosen to be dot
G.layout(prog='dot')

# Write graph to a png file
G.draw('ast_' + file + '.png')
quit("EOF")


