import ast
import os
from typing import Callable

import pygraphviz as pgv
from colorama import Fore, Back, Style


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


# Filter list by given function f
def filter_list(l, f=lambda x: bool(x)):
    return [i for i, x in enumerate(l) if f(x)]


# Extract the edges based on the root node for the CFG
def extract_control_flow(nd: ast.AST, neighbors: list, ref_nodes: list):
    attr_edges_dict = {'color': '#00e629'}
    if len(ref_nodes) > 0 and len(neighbors) == 0 and not isinstance(nd, ast.If or ast.While or ast.For):
        nd_curr = ref_nodes.pop(0)
        edge_list_cfg.append(((nd, nd_curr), attr_edges_dict))
        nd = nd_curr
    if isinstance(nd, ast.Module):
        children = nd.__dict__['body']
        child = children.pop(0)
        edge_list_cfg.append(((nd, child), attr_edges_dict))
        extract_control_flow(child, children, ref_nodes)
    elif isinstance(nd, ast.Assign or ast.AnnAssign or ast.AugAssign):
        if not len(neighbors) == 0:
            neighbor = neighbors.pop(0)
            edge_list_cfg.append(((nd, neighbor), attr_edges_dict))
            extract_control_flow(neighbor, neighbors, ref_nodes)
    elif isinstance(nd, ast.If):
        test = nd.__dict__['test']
        edge_list_cfg.append(((nd, test), attr_edges_dict))

        body = nd.__dict__['body']
        nd_curr = body.pop(0)
        attr_edges_dict = dict()
        attr_edges_dict['color'] = '#00e629'
        attr_edges_dict['label'] = 'T'
        edge_list_cfg.append(((test, nd_curr), attr_edges_dict))
        if len(neighbors) > 0:
            ref_nodes.insert(0, neighbors.pop(0))
        extract_control_flow(nd_curr, body, ref_nodes.copy())

        orelse = nd.__dict__['orelse']
        if len(orelse) > 0:
            nd_curr = orelse.pop(0)
            attr_edges_dict = dict()
            attr_edges_dict['label'] = 'F'
            attr_edges_dict['color'] = '#ff0039'
            edge_list_cfg.append(((test, nd_curr), attr_edges_dict))
            # if len(neighbors) > 0:
            #    ref_nodes.insert(0, neighbors.pop(0))
            extract_control_flow(nd_curr, orelse, ref_nodes.copy())
    elif isinstance(nd, ast.Expr):
        # TODO: Bug over here
        child = nd.__dict__['value']
        edge_list_cfg.append(((nd, child), attr_edges_dict))
        extract_control_flow(child, neighbors, ref_nodes.copy())
    elif isinstance(nd, ast.While):
        neighbor = neighbors.pop(0)
        body = nd.__dict__['body']
        child = body.pop(0)
        edge_list_cfg.append(((nd, child), attr_edges_dict))
        edge_list_cfg.append(((body[-1], nd), attr_edges_dict.copy()))
        edge_list_cfg.append(((nd, neighbor), attr_edges_dict.copy()))
        extract_control_flow(child, body, [])
        extract_control_flow(neighbor, neighbors, [])


# Lists of node in AST and edges
node_list = []
edge_list = []
edge_list_cfg = []
# Define root directory and get list of files in that specific directory
root = '../code_samples/'
files = os.listdir(path=root)

# Print filenames with byte-size in console
print(Back.LIGHTBLACK_EX + Fore.RED + 'Select file index to use:' + Style.RESET_ALL)
for index, file in enumerate(files):
    # Index, Name, Bytes
    print(index, file, os.path.getsize(root + file))

# TODO: file index user input
file_in_use = files[1]
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

# TODO extract control flow graph
extract_control_flow(ast_tree, [], [])
for ((x, y), attr) in edge_list_cfg:
    G.add_edge(node_str_generator(x)[0], node_str_generator(y)[0], **attr)
G.layout(prog='dot')


G.draw('ast_' + file_in_use + '.png')

# Close file reader
os.close(file)
quit("EOF")
