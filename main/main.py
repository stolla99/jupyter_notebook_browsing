import ast
import os
import networkx as nx
import matplotlib.pyplot as plt
from colorama import Fore, Back, Style
from networkx.drawing.nx_agraph import graphviz_layout


def node_str_generator(node):
    if isinstance(node, ast.Module):
        return "root" + str(node)
    elif isinstance(node, ast.Assign):
        return "=" + str(node)
    elif isinstance(node, ast.Name):
        # node = ast.Name(node)
        attributes = node.__dict__
        ident = attributes['id']
        return "var: " + ident + str(node)
    elif isinstance(node, ast.Constant):
        attributes = node.__dict__
        value = attributes['value']
        return "const: " + str(value) + str(node)
    else:
        print("dd")
        return type(node).__name__ + str(node)


# Traverse over tree and add every new node to the list and extend edge list with every
# traversal in child nodes
def node_traversal(nd):
    node_str = node_str_generator(nd)
    if not (node_str in node_list):
        node_list.append(node_str)
    if isinstance(nd, ast.AST):
        lst = ast.iter_fields(nd)
        for field, value in lst:
            if isinstance(value, list):
                for child in value:
                    if isinstance(child, ast.AST):
                        edge_list.append((node_str_generator(nd), node_str_generator(child)))
                        node_traversal(child)
            elif isinstance(value, ast.AST):
                edge_list.append((node_str_generator(nd), node_str_generator(value)))
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

# Create graph from edge list and nodelist using the dot-layout
# TODO: Style tree such it can be read properly
plt.title('AST, file: ' + file_in_use)


graph = nx.DiGraph()
graph.add_edges_from(edge_list)
pos = graphviz_layout(graph, prog='dot')
labels = dict()
for node in node_list:
    labels[node] = node.split('<')[0]
nx.draw(graph, pos,
        with_labels=True,
        labels=labels,
        edgecolors='none',
        node_color='lightgray',
        font_size=10,
        # so^>v<dph8
        node_shape='o',
        node_size=400)

# Save plot in file and show in IDE
plt.savefig('ast_' + file_in_use + '.png')
plt.show()

# Close file reader
os.close(file)
