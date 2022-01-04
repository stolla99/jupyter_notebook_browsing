import ast
import os
from typing import Any, Callable

import pygraphviz as pgv
import difflib as diff
import networkx as nx
import matplotlib.pyplot as plt
from colorama import Fore, Back, Style
from networkx.drawing.nx_agraph import graphviz_layout


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
        # attribute_dict["shape"] = "underline"
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.Name):
        attributes = ast_node.__dict__
        ident = attributes['id']
        label = "Name\\n" + ident
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict
    elif isinstance(ast_node, ast.Constant):
        attributes = ast_node.__dict__
        value = attributes['value']
        label = "Constant\\n" + str(value)
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict
    else:
        label = type(ast_node).__name__
        attribute_dict["label"] = label
        return label + str(ast_node), attribute_dict


# Return false if node is from type ast.Load or ast.Store
type_check_ld_st: Callable[[ast.AST], bool] = lambda arg: not (isinstance(arg, ast.Load) or isinstance(arg, ast.Store))


# Traverse over tree and add every new node to the list and extend edge list with every
# traversal in child nodes
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
                        edge_list.append((node_str_generator(nd)[0], node_str_generator(child)[0]))
                        node_traversal(child)
            elif isinstance(value, ast.AST) and type_check_ld_st(value):
                edge_list.append((node_str_generator(nd)[0], node_str_generator(value)[0]))
                node_traversal(value)


# Lists of node in AST and edges
node_list = []
edge_list = []
# Define root directory and get list of files in that specific directory
root = '../code_samples/'
files = os.listdir(path=root)

# Print filenames with byte-size in console
print(Back.LIGHTBLACK_EX + Fore.RED + 'Select file index to use:' + Style.RESET_ALL)
for index, file in enumerate(files):
    # Index, Name, Bytes
    print(index, file, os.path.getsize(root + file))

# TODO: file index user input
file_in_use = files[0]
# File which is later read
file = os.open(root + file_in_use, os.O_RDONLY)
num_bytes = os.path.getsize(root + file_in_use)

# File as byte string
byte_str = os.read(file, num_bytes).decode("UTF-8")
print("\n" + Back.LIGHTBLACK_EX + Fore.RED + "Program code currently in use for AST:" + Style.RESET_ALL)
print(byte_str)

# Parse AST and traverse the tree by going over every node from source/root
ast_tree = ast.parse(source=byte_str)
node_traversal(ast_tree)

# Clean node and edge list


# Create graph from edge list and nodelist using the dot-layout
G = pgv.AGraph(strict=False, directed=True, label="ast_" + file_in_use)
# Set some default attributes
G.node_attr["shape"] = "Mrecord"
G.graph_attr["rank"] = "same"

# Add edges and nodes with labels
for (node, attr_dict) in node_list:
    G.add_node(node, **attr_dict)
G.add_edges_from(edge_list)
G.layout(prog='dot')


G.draw('ast_' + file_in_use + '.png')

# Close file reader
os.close(file)
quit("EOF")
