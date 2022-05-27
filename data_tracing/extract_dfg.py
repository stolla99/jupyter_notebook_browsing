import ast
import copy
import itertools
import itertools as itera


def child_iter_return(p_nd, node, compare):
    """

    :param compare:
    :param p_nd: node to iterate over
    :param node: Compare node
    :return: Potential parent node
    """
    for child in ast.walk(p_nd):
        if compare(node, child):
            return p_nd
    return None


class DataFlowExtractor:
    """
    Class to extract the data flow based on an AST of all the cells in the jupyter notebook.
    """

    def __init__(self, ast_tree_cells: dict):
        self.ast_tree_cells = ast_tree_cells
        # LIST( TUPLE( node: ast.Name, cell_num: int ) )
        self.ast_name_list = []

        # LIST( TUPLE( TUPLE( node: ast.Name, cell_num: int ), TUPLE( node: ast.Name, cell_num: int ) ) )
        self.ast_edge_list = []

    def walk_and_get_edges(self):
        """
        Walk tree and then return all edges according the data flow.

        :return: List of edges to be added to the graph
        """
        self.walk_tree_by_name()
        self.fill_edge_list()
        return self.ast_edge_list

    def walk_tree_by_name(self, no_dict=False, **kwargs):
        """
        Walks the tree for every cell and inserts ast.Name nodes into the ast_name_list

        :return: List of the all ast.Names found in the ast trees of all cells
        """
        # Simulate the dict
        if no_dict:
            tree = kwargs["ast"]
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and not node in kwargs["to_exclude"]:
                    self.ast_name_list.append((node, kwargs["cell_num"]))
        else:
            for cell_num in self.ast_tree_cells.keys():
                ast_cell = self.ast_tree_cells[cell_num]
                for node in ast.walk(ast_cell):
                    if isinstance(node, ast.Name):
                        self.ast_name_list.append((node, cell_num))
        return self.ast_name_list

    def fill_edge_list(self):
        """
        I dunno know
        """
        sorted_name_list = []
        for iterable, group in itera.groupby(self.ast_name_list, key=lambda elem: elem[1]):
            group = list(group)
            group.sort(key=lambda elem: elem[0].__dict__["lineno"])
            for _, g in itera.groupby(group, key=lambda elem: elem[0].__dict__["lineno"]):
                g = list(g)
                loads = []
                stores = []
                for elem in g:
                    if isinstance(elem[0].__dict__["ctx"], ast.Load):
                        loads.append(elem)
                    else:
                        stores.append(elem)

                sorted_name_list.extend(loads)
                sorted_name_list.extend(stores)
        assert len(sorted_name_list) == len(self.ast_name_list)
        self.ast_name_list = sorted_name_list
        for pos, n_v_tuple in itera.zip_longest(range(len(self.ast_name_list)), self.ast_name_list):
            # ctx is either LOAD, STORE or DEL
            # n_v_tuple[0] -> node
            # n_v_tuple[1] -> origin cell number
            ctx = n_v_tuple[0].__dict__["ctx"]
            identifier = n_v_tuple[0].__dict__["id"]
            if isinstance(ctx, ast.Store):
                rest = list(filter(lambda elem: elem[0].__dict__["id"] == identifier, self.ast_name_list[(pos + 1):]))
                if len(rest) >= 1:
                    first_node_in_rest = rest[0]
                    if isinstance(first_node_in_rest[0].__dict__["ctx"], ast.Load):
                        self.ast_edge_list.append((n_v_tuple, rest[0]))
                        self._add_to_list(rest)

    def _add_to_list(self, rest: [ast.AST]):
        # n_v_tpl_tail is implicitly always form instance ast.Load due to the function call if procedure
        for n_v_tpl_tail, n_v_tpl_head in itertools.pairwise(rest):
            ctx_head = n_v_tpl_head[0].__dict__["ctx"]
            if isinstance(ctx_head, ast.Load):
                self.ast_edge_list.append((n_v_tpl_tail, n_v_tpl_head))
            else:
                # In case the node n_v_tpl_head has the type ast.Store or ast.Del we can break an exit the function.
                # ast.Store -> Variable will be overwritten
                # ast.Del   -> Variable will be destroyed for the remaining script
                break

    def get_parent_node(self, node: ast.AST, ast_nodes: [ast.AST], compare=lambda x, y: x == y):
        """

        :param compare:
        :param ast_nodes:
        :param node:
        """
        for ast_node in ast_nodes:
            if not (isinstance(ast_node, ast.FunctionDef) or isinstance(ast_node, ast.Return)):
                if isinstance(ast_node, ast.For):
                    cpy = copy.deepcopy(ast_node)
                    cpy.body.clear()
                    for child in ast.walk(cpy):
                        if compare(node, child):
                            return ast_node
                elif isinstance(ast_node, ast.If):
                    # If variable is in test then it can't be in the body or "orelse" part.
                    for component in [ast_node.body, ast_node.orelse, ast_node]:
                        if isinstance(component, list):
                            for line in component:
                                parent = child_iter_return(line, node, compare)
                                if parent is not None:
                                    return parent
                        else:
                            parent = child_iter_return(component, node, compare)
                            if parent is not None:
                                return parent
                else:
                    for child in ast.walk(ast_node):
                        if compare(node, child):
                            return ast_node
        return None
