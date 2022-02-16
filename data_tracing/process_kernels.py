import os
import ast
import pygraphviz as pgv
from typing import Callable
from nbformat import read, NO_CONVERT
import itertools


def pairwise(iterable):
    """
    Copied from the python 3.10 itertools library
    :param iterable:
    :return:
    """
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


type_check_ld_st: Callable[[ast.AST], bool] = lambda arg: not (isinstance(arg, ast.Load) or isinstance(arg, ast.Store)
                                                               or isinstance(arg, ast.operator)
                                                               or isinstance(arg, ast.unaryop))


def node_str_generator(ast_node, current_cell):
    """

    :param current_cell: Current cell resulting from the notebook.
    :param ast_node: Node from the ast which has all the information to create a label for the graph
    :return: name for the node in the graph and dictionary with attributes
    """
    cell_str = "$cell" + str(current_cell)
    attribute_dict = dict()
    attribute_dict["margin"] = "0,0"
    if isinstance(ast_node, ast.Module):
        label = "Module"
        attribute_dict["label"] = label
        attribute_dict["style"] = "invis"
    elif isinstance(ast_node, ast.FunctionDef):
        attributes = ast_node.__dict__
        label = "FunctionDef\\n="
        name = attributes['name']
        attribute_dict["label"] = label + name
    elif isinstance(ast_node, ast.Assign):
        label = "Assign\\n="
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.Name):
        attributes = ast_node.__dict__
        ident = attributes['id']
        label = "Name\\n" + ident
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.ImportFrom):
        attributes = ast_node.__dict__
        module = attributes['module']
        label = "ImportFrom\\n" + str(module)
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.Constant):
        attributes = ast_node.__dict__
        value = attributes['value']
        label = "Constant\\n" + str(value)
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.Attribute):
        attributes = ast_node.__dict__
        attr = attributes['attr']
        label = "Attribute\\n" + str(attr)
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.alias):
        attributes = ast_node.__dict__
        asname = attributes['asname']
        name = attributes['name']
        if asname is None:
            label = "alias\\n" + str(name)
        else:
            label = "alias\\n" + str(name) + " as " + str(asname)
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.keyword):
        attributes = ast_node.__dict__
        arg = attributes['arg']
        label = "keyword\\n" + "arg " + str(arg)
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.arg):
        attributes = ast_node.__dict__
        arg = attributes['arg']
        label = "arg\\n" + str(arg)
        attribute_dict["label"] = label
    elif isinstance(ast_node, ast.BinOp):
        attributes = ast_node.__dict__
        label = "BinOp\\n"
        operator = type(attributes['op']).__name__
        attribute_dict["label"] = label + operator
    elif isinstance(ast_node, ast.AugAssign):
        attributes = ast_node.__dict__
        label = "AugAssign\\n"
        operator = type(attributes['op']).__name__
        attribute_dict["label"] = label + operator
    elif isinstance(ast_node, ast.UnaryOp):
        attributes = ast_node.__dict__
        label = "UnaryOp\\n"
        operator = type(attributes['op']).__name__
        attribute_dict["label"] = label + operator
    else:
        label = type(ast_node).__name__
        attribute_dict["label"] = label
    return label + str(ast_node) + cell_str, attribute_dict


def node_traversal(nd, current_cell):
    """
    Function traverses the ast of the code beginning from the module node of the ast. Each ast corresponds
    to a code cell in the jupyter notebook file.

    :param current_cell: Cell in which the ast is traversed, cell from the notebook
    :param nd: current node in the ast
    """
    node_str, attribute_dict = node_str_generator(nd, current_cell)
    if not (node_str in node_list) and type_check_ld_st(nd):
        node_list.append((node_str, attribute_dict))
    if isinstance(nd, ast.AST):
        lst = ast.iter_fields(nd)
        for field, value in lst:
            if isinstance(value, list):
                for child in value:
                    if isinstance(child, ast.AST) and type_check_ld_st(child):
                        edge_list.append((node_str, node_str_generator(child, current_cell)[0]))
                        node_traversal(child, current_cell)
            elif isinstance(value, ast.AST) and type_check_ld_st(value):
                edge_list.append((node_str, node_str_generator(value, current_cell)[0]))
                node_traversal(value, current_cell)


file = 'data_vis_exer_1'
ext = '.ipynb'
path = '../notebooks/'
dir_list = os.listdir(path)
print(dir_list)
# TODO: Convert all

with open(path + file + ext) as fp:
    notebook = read(fp, NO_CONVERT)
cells = notebook['cells']
code_cells = [c for c in cells if c['cell_type'] == 'code']

# One ast for every code cell
ast_dict = dict()
# Node and edge lists
node_list = []
edge_list = []
cluster_head_list = []

for cell, i in itertools.zip_longest(code_cells, range(len(code_cells))):
    source = cell['source']
    try:
        ast_cell = ast.parse(source=source)
        print(source)
    except SyntaxError:
        print('Parsing failed with SyntaxError')
        ast_cell = ast.parse(source='\n')
    node_traversal(ast_cell, i)
    ast_dict[str(i)] = (node_list.copy(), edge_list.copy())
    node_list.clear()
    edge_list.clear()

# Create graph from edge list and nodelist using the dot-layout
G = pgv.AGraph(strict=False, directed=True, label="ast_" + file, compound=True, rankdir="TB", splines="polyline")
# Set some default attributes
G.node_attr['shape'] = 'Mrecord'

# Add edges and nodes with labels
for cell_key in ast_dict.keys():
    cell_code = ast_dict[cell_key]
    # Adding cluster anchor nodes with the corresponding cell number (node_str, cell_num)
    cluster_head_list.append(((cell_code[0])[0])[0])
    for (node, attr_dict) in cell_code[0]:
        G.add_node(node, **attr_dict)

for cell_key in ast_dict.keys():
    cell_code = ast_dict[cell_key]
    name = 'Cell ' + cell_key
    G.subgraph(list(map(lambda elem: elem[0], cell_code[0])), name="cluster"+cell_key, label=name, rank="same")

for cell_key in ast_dict.keys():
    cell_code = ast_dict[cell_key]
    for u, v in cell_code[1]:
        if u in cluster_head_list:
            G.add_edge(u, v, style="invis")
        else:
            G.add_edge(u, v)

G.add_subgraph(cluster_head_list, rank="same")
G.layout(prog='dot')
G.draw('ast_' + file + '.png')
quit("EOF")
