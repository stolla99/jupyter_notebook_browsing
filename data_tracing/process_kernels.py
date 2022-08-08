import ast
import copy
import csv
import itertools
import os
import subprocess
import time

import matplotlib.pyplot as plt
import pygraphviz as pgv
import squarify
from alive_progress import alive_bar
from bs4 import BeautifulSoup
from nbformat import read, NO_CONVERT

from data_tracing.extract_cfg import ControlFlowExtractor
from data_tracing.extract_dfg import DataFlowExtractor

type_check_ld_st = lambda arg: not (isinstance(arg, ast.Load)
                                    or isinstance(arg, ast.Store)
                                    or isinstance(arg, ast.operator)
                                    or isinstance(arg, ast.unaryop))


def cmp_on_id_lvl(nd_x, nd_y):
    """

    :param nd_x:
    :param nd_y:
    :return:
    """
    if isinstance(nd_x, ast.Name) and isinstance(nd_y, ast.Name):
        return nd_x.id == nd_y.id
    else:
        return False


def count_name_occurence(alias_: str, cell_: ast.AST):
    """
    Counts occurrences of every alias in the AST of one cell. Returns the count.

    :param alias_: alias to count over
    :param cell_: ast with nodes to iterate over
    """
    counter = 0
    for child_ in ast.walk(cell_):
        if isinstance(child_, ast.Name):
            if child_.id == alias_:
                counter += 1
    return counter


def get_all_alias(cell_: ast.AST):
    """

    :param cell_:
    """
    for child_ in ast.walk(cell_):
        if isinstance(child_, ast.alias):
            if child_.asname is not None:
                yield child_.asname
            else:
                yield child_.name


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
        label = ''
        attribute_dict["label"] = label
        attribute_dict["shape"] = "plaintext"
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


def update_html(n_attr, name, n_v_tuple):
    """

    :param n_attr:
    :return:
    """
    html_str = n_attr["label"]
    soup = BeautifulSoup(html_str, features="lxml")
    for repElem in soup.find_all("td"):
        if "port" in repElem.attrs.keys():
            if trim_string(name) == repElem.attrs["port"]:
                repElem.attrs["color"] = look_up_color[n_v_tuple[0].id]
    html_str_updated = "<" + str(soup.find("table")) + ">"
    n_attr["label"] = html_str_updated
    return n_attr


def parse_list(line_list):
    """
    Iterates over of string and yield every successful parsed line.

    :param line_list:
    """
    for elem in line_list:
        try:
            _ = ast.parse(source=elem)
            yield elem
        except SyntaxError:
            print('SyntaxError due to line: ' + elem + '\n')


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
        to_exclude = []
        for target in node.targets:
            for child in ast.walk(target):
                if isinstance(child, ast.Name):
                    to_exclude.append(child)
        dfg_node_list = dfg_ex.walk_tree_by_name(no_dict=True, ast=node, cell_num=cell_key, to_exclude=to_exclude)
        rowspan = 2
        if len(dfg_node_list) == 0:
            rowspan = 1
        target_string = "<<TABLE WIDTH=\"\" BORDER=\"0\" CELLBORDER=\"1\" CELLSPACING=\"4\" CELLPADDING=\"4\">" \
                        + "<TR>" \
                        + "".join(["<TD STYLE=\"ROUNDED\" ROWSPAN=\"" + str(rowspan)
                                   + "\" PORT=\"" + trim_string(node_str_generator(n, cell_key)[0])
                                   + "\">"
                                   + prepare_html((node_str_generator(n, cell_key)[1])["label"])
                                   + "</TD>"
                                   for n in to_exclude]) \
                        + "<TD STYLE=\"ROUNDED\" COLSPAN=\"" + str(max(1, len(dfg_node_list))) + "\">" \
                        + prepare_html((node_str_generator(node.value, cell_key)[1])["label"]) \
                        + "</TD>" \
                        + "</TR>"
        used_var_str = ""
        if len(dfg_node_list) > 0:
            used_var_str += "<TR>" + "".join(["<TD STYLE=\"ROUNDED\" PORT=\""
                                              + trim_string(node_str_generator(n, int(val))[0])
                                              + "\">"
                                              + prepare_html((node_str_generator(n, int(val))[1])["label"])
                                              + "</TD>"
                                              for n, val in dfg_node_list]) + "</TR>"
        label = target_string + used_var_str + "</TABLE>>"
        attr_node_dict["label"] = label
    elif isinstance(node, ast.Expr):
        dfg_node_list = dfg_ex.walk_tree_by_name(no_dict=True, ast=node, cell_num=cell_key, to_exclude=[])
        label = prepare_html((node_str_generator(node, cell_key)[1])["label"])
        label = "<<TABLE WIDTH=\"\" BORDER=\"0\" CELLBORDER=\"1\" CELLSPACING=\"4\" " \
                + "CELLPADDING=\"4\">" \
                + "<TR><TD STYLE=\"ROUNDED\" COLSPAN=\"" \
                + str(max(1, len(dfg_node_list))) + "\">" + label + "</TD></TR>"
        if len(dfg_node_list) > 0:
            label += "<TR>" + "".join(["<TD STYLE=\"ROUNDED\" PORT=\""
                                       + trim_string(node_str_generator(var, cell_key)[0])
                                       + "\">"
                                       + prepare_html(((node_str_generator(var, cell_num))[1])["label"])
                                       + "</TD>"
                                       for var, cell_num in dfg_node_list]) + "</TR></TABLE>>"
        else:
            label += "</TABLE>>"
        attr_node_dict["label"] = label
    elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
        # Alias are not tracked throughout the document
        label = "<<TABLE STYLE=\"ROUNDED\" WIDTH=\"\" BORDER=\"0\" CELLBORDER=\"1\" CELLSPACING=\"4\" " \
                + "CELLPADDING=\"4\">" \
                + "<TR><TD STYLE=\"ROUNDED\">" + prepare_html((node_str_generator(node, cell_key)[1])["label"]) \
                + "</TD></TR></TABLE>>"
        attr_node_dict["label"] = label
    elif isinstance(node, ast.If) or isinstance(node, ast.For):
        table_head = "IF"
        to_exclude = []
        if isinstance(node, ast.For):
            table_head = "FOR"
            test = node
            for line in test.body:
                for child in ast.walk(line):
                    if isinstance(child, ast.Name):
                        to_exclude.append(child)
        else:
            test = node.__dict__['test']
        dfg_node_list = dfg_ex.walk_tree_by_name(no_dict=True, ast=test, cell_num=cell_key, to_exclude=to_exclude)
        label = prepare_html((node_str_generator(test, cell_key)[1])["label"])
        rowspan = 2
        if len(dfg_node_list) == 0:
            rowspan = 1
        label = "<<TABLE WIDTH=\"\" BORDER=\"0\" CELLBORDER=\"1\" CELLSPACING=\"4\" CELLPADDING=\"4\">" \
                + "<TR><TD STYLE=\"ROUNDED\" ROWSPAN=\"" + str(rowspan) + "\">" + table_head + "</TD>" \
                + "<TD STYLE=\"ROUNDED\" COLSPAN=\"" \
                + str(max(1, len(dfg_node_list))) + "\">" + label + "</TD></TR>"
        if len(dfg_node_list) > 0:
            label += "<TR>" + "".join(["<TD STYLE=\"ROUNDED\" PORT=\""
                                       + trim_string(node_str_generator(var, cell_key)[0])
                                       + "\">"
                                       + prepare_html(((node_str_generator(var, cell_num))[1])["label"])
                                       + "</TD>"
                                       for var, cell_num in dfg_node_list]) + "</TR></TABLE>>"
        else:
            label += "</TABLE>>"
        attr_node_dict["label"] = label

    return node_str_generator(node, cell_key)[0], attr_node_dict


if __name__ == "__main__":
    ext = '.ipynb'
    path = '../notebooks/'
    dir_list = os.listdir(path)
    print("Files in directory:")
    for i in range(len(dir_list)):
        print(str(i) + ": " + str(dir_list[i]))

    file = "example_notebook_overview.ipynb"

    not_chosen = True
    while not_chosen:
        file_index = input("\nChoose file from [0," + str(len(dir_list)-1) + "]:")
        try:
            if 0 <= int(file_index) < len(dir_list):
                file = dir_list[int(file_index)]
                not_chosen = False
            else:
                print("Index " + str(file_index) + " out of bounds")
        except ValueError as ex:
            print(ex.__str__())

    with open(path + file) as fp:
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
            # print(source + '\n')
        except SyntaxError:
            print('Cell: Parsing failed with SyntaxError')
            lst = list(parse_list(source.split('\n')))
            new_source_code = '\n'.join(lst)
            ast_cell = ast.parse(source=new_source_code)
            del lst
            del new_source_code
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
    last_line_nodes = []

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
            skip_first_cell = False

            if cell_key == str(0):
                if all(map(lambda elem: isinstance(elem, ast.Import)
                                        or isinstance(elem, ast.ImportFrom),
                           cfg_ex.get_nodes(skip_module=True))):
                    skip_first_cell = True
                    list_of_alias = [alias for alias in get_all_alias(ast_cell)]
                    occurence_dict = {key: 0 for key in list_of_alias}
                    for cell_num in range(1, len(ast_dict_parsed.keys())):
                        ast_cell_ = ast_dict_parsed[str(cell_num)]
                        for alias in list_of_alias:
                            count = count_name_occurence(alias, ast_cell_)
                            occurence_dict[alias] += count
                    # Delete keys with value == 0
                    to_pop = []
                    for key in occurence_dict.keys():
                        if occurence_dict[key] == 0:
                            to_pop.append(key)
                    for key in to_pop:
                        occurence_dict.pop(key)
                    labels = [key + "(" + str(value) + ")" for key, value in zip(occurence_dict.keys(),
                                                                                 occurence_dict.values())]
                    squarify.plot(sizes=occurence_dict.values(), label=labels, alpha=0.6)
                    plt.axis('off')
                    image_path = '../output/plot_' + file + '.png'
                    plt.savefig(image_path, bbox_inches='tight')
                    edge_list = list(filter(lambda elem: isinstance((elem[0])[0], ast.Module), edge_list))
                    if len(edge_list) == 1:
                        node = ((edge_list[0])[0])[1]
                        node_str, attr_dict = node_str_generator(node, cell_key)
                        attr_dict['label'] = ''
                        attr_dict['image'] = image_path
                        G.add_node(node_str, **attr_dict)
                        cfg_ex.edge_list_cfg = edge_list
                        ast_cfg_nodes_dict[cell_key] = [node]

            for node in cfg_ex.get_nodes():
                if isinstance(node, ast.Module):
                    cluster_head = node
                    nodes.append(node_str_generator(node, cell_key))
                elif isinstance(node, ast.Assign) or isinstance(node, ast.Expr):
                    html_nodes.append(process_node(node, cell_key))
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    if not skip_first_cell:
                        html_nodes.append(process_node(node, cell_key))
                    else:
                        node_str, attr_dict = node_str_generator(node, cell_key)
                        attr_dict['label'] = ""
                        nodes.append((node_str, attr_dict))
                elif isinstance(node, ast.If) or isinstance(node, ast.For):
                    html_nodes.append(process_node(node, cell_key))
                else:
                    nodes.append(node_str_generator(node, cell_key))

            # Create html_doc to render and obtain max offsetWidth to ensure left alignment of tables in nodes of the graph
            html_doc = ""
            for (node_str, attr_dict) in html_nodes:
                html_str = attr_dict["label"]
                html_doc += html_str[1:len(html_str) - 1]

            max_width = 0
            """if html_doc == "":
                max_width = 0
            else:
                max_width = get_width_of_table(html_doc)"""
            for (node_str, attr_dict) in html_nodes:
                label = attr_dict["label"]
                attr_dict["label"] = label.replace("WIDTH=\"\"", "WIDTH=\"" + str(max_width) + "\"")
                nodes.append((node_str, attr_dict))
            html_nodes.clear()

            cfg_nodes_sorted = ast_cfg_nodes_dict[cell_key]
            cfg_nodes_sorted.sort(key=lambda elem: elem.__dict__["lineno"])
            previous_node_str = None
            first = True
            for node, cell_num in itertools.zip_longest(cfg_nodes_sorted, range(len(cfg_nodes_sorted))):
                label_ext = ""
                lineno = str(node.__dict__["lineno"])
                end_lineno = str(node.__dict__["end_lineno"])
                # if lineno == end_lineno:
                label_ext += lineno
                # else:
                #     label_ext += lineno + "-" + end_lineno
                node_str = node_str_generator(node, cell_key)[0] + "$line" + label_ext
                if first:
                    line_nodes.append(node_str)
                    first = False
                if cell_num == len(cfg_nodes_sorted) - 1:
                    last_line_nodes.append(node_str)
                color = "grey"
                if node in cfg_ex.true_list:
                    color = "green"
                elif node in cfg_ex.false_list:
                    color = "red"
                font_string = "<B>Line</B> " + label_ext + ":"
                if int(cell_key) == 0 and skip_first_cell:
                    font_string = "<B>Overview</B>"
                nodes.append((node_str,
                              {
                                  "label": "<<FONT COLOR=\"grey\" FACE=\"Monospace\">" + font_string + "</FONT>>",
                                  "shape": "plaintext"}))
                edge_list.append(((node_str, node), {"color": color, "constraint": "False", "arrowhead": "none"}))
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

    # Ensure that cells are displayed from left to right in the graph => Place Module node of every cell onto the
    # same level
    dummy_nodes = []
    first = True
    i = 0
    attr = {"color": "grey", "arrowhead": "none", "weight": "3"}
    if len(cluster_head_list) == 1:
        x = cluster_head_list[0]
        x_str = node_str_generator(x[0], x[1])[0]
        x_str_ext = x_str + "$line" + str(x[1])
        G.add_node(x_str_ext, label="")
        if not G.has_edge(x_str_ext, x_str):
            G.add_edge(x_str_ext, x_str, style="invis")
        dummy_nodes.append(x_str + "$line" + str(x[1]))
    else:
        for x, y in itertools.pairwise(cluster_head_list):
            x_str = node_str_generator(x[0], x[1])[0]
            y_str = node_str_generator(y[0], y[1])[0]
            x_str_ext = x_str + "$line" + str(x[1])
            y_str_ext = y_str + "$line" + str(y[1])
            if first:
                dummy_nodes.append(x_str_ext)
                first = False
            dummy_nodes.append(y_str_ext)
            G.add_node(x_str_ext, label="")
            G.add_node(y_str_ext, label="")
            if not G.has_edge(x_str_ext, x_str):
                G.add_edge(x_str_ext, x_str, style="invis")
            G.add_edge(last_line_nodes[i], y_str_ext, **attr)
            if i == len(cluster_head_list) - 2:
                G.add_edge(y_str_ext, y_str, style="invis")
            i += 1

    # Prepare the head list and extend with dummy nodes
    head_nodes = [node_str_generator(node, cell)[0] for (node, cell) in cluster_head_list]
    # assert len(dummy_nodes) == len(line_nodes)
    for dummy, head in itertools.zip_longest(dummy_nodes, head_nodes):
        G.add_subgraph([dummy, head], rank="same")

    for dummy, line in itertools.zip_longest(dummy_nodes, line_nodes):
        G.add_edge(dummy, line, **attr)

    # Colors for color coding from lookup table
    # Each variable name has its own color if all colors are assigned colors will be reused
    look_up_color = dict()
    # Current index in the color palette
    curr_color_i = 0
    csv_file = open('../resources/colors.csv', newline='')
    color_palette = csv.reader(csv_file, delimiter=' ')
    colors = [c[0] for c in color_palette]
    csv_file.close()

    attr = {"constraint": "False", "arrowsize": "0.65"}
    dfg_ex = DataFlowExtractor(ast_dict_parsed)
    dfg_edge_list = dfg_ex.walk_and_get_edges()
    # Save every variable for every node
    node_var_dict = dict()

    for n_v_tupleU, n_v_tupleV in dfg_edge_list:
        parent_U = dfg_ex.get_parent_node(n_v_tupleU[0], ast_cfg_nodes_dict[n_v_tupleU[1]])
        parent_V = dfg_ex.get_parent_node(n_v_tupleV[0], ast_cfg_nodes_dict[n_v_tupleV[1]])
        if parent_U is None:
            parent_U = dfg_ex.get_parent_node(n_v_tupleU[0], ast_cfg_nodes_dict[n_v_tupleU[1]], compare=cmp_on_id_lvl)
        elif parent_V is None:
            parent_V = dfg_ex.get_parent_node(n_v_tupleV[0], ast_cfg_nodes_dict[n_v_tupleV[1]], compare=cmp_on_id_lvl)
        if parent_V is None or parent_U is None:
            # TODO eval function def edges
            continue
        elif parent_U == parent_V:
            if n_v_tupleU[1] < n_v_tupleV[1]:
                print("found" + n_v_tupleU[1] + " " + n_v_tupleV[1])
            continue
        else:
            name = n_v_tupleU[0].id
            nameU, _ = node_str_generator(n_v_tupleU[0], n_v_tupleU[1])
            nameV, _ = node_str_generator(n_v_tupleV[0], n_v_tupleV[1])
            if name in look_up_color.keys():
                attr["color"] = look_up_color[name]
            else:
                color = colors[curr_color_i]
                look_up_color[name] = color
                attr["color"] = color
                curr_color_i = (curr_color_i + 1) % len(colors)
            # n_v_tupleX[1] is always the cell number.
            if int(n_v_tupleU[1]) < int(n_v_tupleV[1]):
                node_str = head_nodes[int(n_v_tupleV[1])]
                if node_str in node_var_dict.keys():
                    vari = node_var_dict[node_str]
                    vari.append(name)
                    node_var_dict[node_str] = vari
                else:
                    node_var_dict[node_str] = [name]
                head = G.get_node(node_str)
                attrs = head.attr.to_dict()
                attr_in = attr.copy()
                attr_in['arrowhead'] = "dot"
                G.add_edge(node_str_generator(parent_U, n_v_tupleU[1])[0],
                           node_str,
                           tailport=trim_string(nameU) + ":" + "s",
                           headport=trim_string(name + "$input") + ":" + "w",
                           **attr_in)

                # Updating the HTML string
                node_attr = G.get_node(node_str_generator(parent_U, n_v_tupleU[1])[0]).attr.to_dict()
                G.add_node(node_str_generator(parent_U, n_v_tupleU[1])[0], **update_html(node_attr, nameU, n_v_tupleU))

                attr_out = attr.copy()
                attr_out['arrowhead'] = "normal"
                attr_out['arrowtail'] = "dot"
                attr_out['dir'] = "both"
                G.add_edge(node_str,
                           node_str_generator(parent_V, n_v_tupleV[1])[0],
                           tailport=trim_string(name + "$output") + ":" + "e",
                           headport=trim_string(nameV) + ":" + "n",
                           **attr_out)

                # Updating the HTML string
                node_attr = G.get_node(node_str_generator(parent_V, n_v_tupleV[1])[0]).attr.to_dict()
                G.add_node(node_str_generator(parent_V, n_v_tupleV[1])[0], **update_html(node_attr, nameV, n_v_tupleV))
            else:
                G.add_edge(node_str_generator(parent_U, n_v_tupleU[1])[0],
                           node_str_generator(parent_V, n_v_tupleV[1])[0],
                           tailport=trim_string(nameU) + ":" + "s",
                           headport=trim_string(nameV) + ":" + "n",
                           **attr)

                # Updating the HTML string
                node_attr = G.get_node(node_str_generator(parent_U, n_v_tupleU[1])[0]).attr.to_dict()
                G.add_node(node_str_generator(parent_U, n_v_tupleU[1])[0], **update_html(node_attr, nameU, n_v_tupleU))
                node_attr = G.get_node(node_str_generator(parent_V, n_v_tupleV[1])[0]).attr.to_dict()
                G.add_node(node_str_generator(parent_V, n_v_tupleV[1])[0], **update_html(node_attr, nameV, n_v_tupleV))

    for (key, var_list) in node_var_dict.items():
        attrs = {'shape': 'plaintext', 'margin': '0.1'}
        label = "<<TABLE STYLE=\"ROUNDED\" BORDER=\"1\" CELLBORDER=\"0\" CELLSPACING=\"0\" CELLPADDING=\"4\">"
        for var in var_list:
            label += "<TR>" \
                     + "<TD WIDTH=\"10\" HEIGHT=\"10\" FIXEDSIZE=\"TRUE\" PORT=\"" + trim_string(var + "$input") \
                     + "\"></TD>" \
                     + "<TD>" + var + "</TD>" \
                     + "<TD WIDTH=\"10\" HEIGHT=\"10\" FIXEDSIZE=\"TRUE\" PORT=\"" \
                     + trim_string(var + "$output") + "\"></TD></TR>"
        label += "</TABLE>>"
        attrs['label'] = label
        G.add_node(key, **attrs)

    # Layout chosen to be dot
    G.layout(prog='dot')

    # Write graph to a png file
    G.draw('../output/vis_' + file + '.pdf')
    G.draw('../output/vis_' + file + '.png')
    print("EOF")
