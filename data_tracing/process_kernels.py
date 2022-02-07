import os
import ast
import pygraphviz as pgv
from typing import Callable
from nbformat import read, NO_CONVERT
import itertools as iter
from collections import Counter

"""
Return false if node is from type ast.Load or ast.Store
"""
type_check_ld_st: Callable[[ast.AST], bool] = lambda arg: not (isinstance(arg, ast.Load) or isinstance(arg, ast.Store)
                                                               or isinstance(arg, ast.operator)
                                                               or isinstance(arg, ast.unaryop))

"""
Docstring
"""
def node_str_generator(ast_node):
    attribute_dict = dict()
    attribute_dict["margin"] = "0,0"
    label = ""
    if isinstance(ast_node, ast.Module):
        label = "Module"
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.Assign):
        label = "Assign\\n="
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.Name):
        attributes = ast_node.__dict__
        ident = attributes['id']
        label = "Name\\n" + ident
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.ImportFrom):
        attributes = ast_node.__dict__
        module = attributes['module']
        label = "ImportFrom\\n" + str(module)
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.Constant):
        attributes = ast_node.__dict__
        value = attributes['value']
        label = "Constant\\n" + str(value)
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.Attribute):
        attributes = ast_node.__dict__
        attr = attributes['attr']
        label = "Attribute\\n" + str(attr)
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.alias):
        attributes = ast_node.__dict__
        asname = attributes['asname']
        name = attributes['name']
        if asname is None:
            label = "alias\\n" + str(name)
        else:
            label = "alias\\n" + str(name) + " as " + str(asname)
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.keyword):
        attributes = ast_node.__dict__
        arg = attributes['arg']
        label = "keyword\\n" + "arg " + str(arg)
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.BinOp):
        attributes = ast_node.__dict__
        label = "BinOp\\n"
        operator = type(attributes['op']).__name__
        attribute_dict["label"] = label + operator
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.AugAssign):
        attributes = ast_node.__dict__
        label = "AugAssign\\n"
        operator = type(attributes['op']).__name__
        attribute_dict["label"] = label + operator
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.UnaryOp):
        attributes = ast_node.__dict__
        label = "UnaryOp\\n"
        operator = type(attributes['op']).__name__
        attribute_dict["label"] = label + operator
        return label + str(ast_node), attribute_dict
    else:
        label = type(ast_node).__name__
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict


"""
Traverse over tree and add every new node to the list and extend edge list with every
traversal in child nodes
"""


def node_traversal(nd):
    node_str, attribute_dict = node_str_generator(nd)
    if not (node_str in node_list) and type_check_ld_st(nd):
        node_list.append((node_str, attribute_dict))
    if isinstance(nd, ast.AST):
        lst = ast.iter_fields(nd)
        for field, value in lst:
            if isinstance(value, list):
                for child in value:
                    if isinstance(child, ast.AST) and type_check_ld_st(child):
                        edge_list.append((node_str, node_str_generator(child)[0]))
                        node_traversal(child)
            elif isinstance(value, ast.AST) and type_check_ld_st(value):
                edge_list.append((node_str, node_str_generator(value)[0]))
                node_traversal(value)


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

for cell, i in iter.zip_longest(code_cells, range(len(code_cells))):
    source = cell['source']
    try:
        ast_cell = ast.parse(source=source)
        print(source)
    except SyntaxError:
        print('Parsing failed with SyntaxError')
        ast_cell = ast.parse(source='\n')
    node_traversal(ast_cell)
    ast_dict[str(i)] = (node_list.copy(), edge_list.copy())
    node_list.clear()
    edge_list.clear()

# Create graph from edge list and nodelist using the dot-layout
G = pgv.AGraph(strict=False, directed=True, label="ast_" + file)
# Set some default attributes
G.node_attr['shape'] = 'Mrecord'
G.graph_attr['rank'] = 'same'
G.graph_attr['compound'] = True

# Add edges and nodes with labels
for cell_key in ast_dict.keys():
    cell_code = ast_dict[cell_key]
    for (node, attr_dict) in cell_code[0]:
        G.add_node(node, **attr_dict)
    G.add_edges_from(cell_code[1])

# Add clusters

G.layout(prog='dot')
G.draw('ast_' + file + '.png')
del G

quit("EOF")
