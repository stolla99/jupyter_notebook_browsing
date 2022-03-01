import ast
import itertools
from _ast import AST


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
        for pos, n_v_tuple in itertools.zip_longest(range(len(self.ast_name_list)), self.ast_name_list):
            # ctx is either LOAD, STORE or DEL
            # n_v_tuple[0] -> node
            # n_v_tuple[1] -> origin cell number
            ctx = n_v_tuple[0].__dict__["ctx"]
            identifier = n_v_tuple[0].__dict__["id"]
            if isinstance(ctx, ast.Store):
                rest = list(filter(lambda elem: elem[0].__dict__["id"] == identifier, self.ast_name_list[(pos+1):]))
                self._add_to_list(n_v_tuple, rest)

    def _add_to_list(self, source: ast.AST, rest: [ast.AST]):
        for n_v_tuple in rest:
            ctx = n_v_tuple[0].__dict__["ctx"]
            if isinstance(ctx, ast.Load):
                self.ast_edge_list.append((source, n_v_tuple))
            else:
                # In case the node has the type ast.Store or ast.Del we can break an exit the function.
                # ast.Store -> Variable is overwritten
                # ast.Del -> Variable is destroyed for the remaining script
                break
