import ast
import itertools as iter
import data_tracing.utils as utils


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

    def walk_tree_by_name(self):
        """
        Walks the tree for every cell and inserts ast.Name nodes into the ast_name_list

        :return: List of the all ast.Names found in the ast trees of all cells
        """
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
        for iterable, group in iter.groupby(self.ast_name_list, key=lambda elem: elem[1]):
            group = list(group)
            group.sort(key=lambda elem: elem[0].__dict__["lineno"])
            sorted_name_list.extend(group)
            print("")
        assert len(sorted_name_list) == len(self.ast_name_list)
        self.ast_name_list = sorted_name_list
        for pos, n_v_tuple in iter.zip_longest(range(len(self.ast_name_list)), self.ast_name_list):
            # ctx is either LOAD, STORE or DEL
            # n_v_tuple[0] -> node
            # n_v_tuple[1] -> origin cell number
            ctx = n_v_tuple[0].__dict__["ctx"]
            identifier = n_v_tuple[0].__dict__["id"]
            if isinstance(ctx, ast.Store):
                rest = list(filter(lambda elem: elem[0].__dict__["id"] == identifier, self.ast_name_list[(pos+1):]))
                if len(rest) >= 1:
                    first_node_in_rest = rest[0]
                    if isinstance(first_node_in_rest[0].__dict__["ctx"], ast.Load):
                        self.ast_edge_list.append((n_v_tuple, rest[0]))
                        self._add_to_list(rest)

    def _add_to_list(self, rest: [ast.AST]):
        # n_v_tpl_tail is implicitly always form instance ast.Load due to the function call if procedure
        for n_v_tpl_tail, n_v_tpl_head in utils.pairwise(rest):
            ctx_head = n_v_tpl_head[0].__dict__["ctx"]
            if isinstance(ctx_head, ast.Load):
                self.ast_edge_list.append((n_v_tpl_tail, n_v_tpl_head))
            else:
                # In case the node n_v_tpl_head has the type ast.Store or ast.Del we can break an exit the function.
                # ast.Store -> Variable will be overwritten
                # ast.Del   -> Variable will be destroyed for the remaining script
                break
