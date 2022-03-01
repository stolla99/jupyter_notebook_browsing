import ast


class ControlFlowExtractor:
    """
    Class to extract the control based on an AST.
    """

    def __init__(self):
        self.edge_list_cfg = []

    def get_nodes(self):
        """

        :return:
        """
        temp = set()
        for ((x, y), attr) in self.edge_list_cfg:
            temp.add(x)
            temp.add(y)
        return temp

    def get_edge_list(self, with_attributes=True):
        """

        :param with_attributes:
        :return:
        """
        if with_attributes:
            return self.edge_list_cfg
        else:
            temp = []
            for ((x, y), _) in self.edge_list_cfg:
                temp.append((x, y))
            return temp

    def extract_CFG(self, nd: ast.AST):
        """

        :param nd:
        """
        self.edge_list_cfg.clear()
        attr_edges_dict = {'color': '#00e629'}
        if isinstance(nd, ast.Module):
            body = nd.__dict__['body']
            if len(body) > 0:
                self.edge_list_cfg.append(((nd, body[0]), attr_edges_dict.copy()))
                # lst = self.create_CFG(body)
                self.create_CFG(body)
            else:
                print('Empty file')
        else:
            print('No module found')

    def create_CFG(self, body: list):
        """

        :param body:
        :return:
        """
        for i in range(0, len(body)):
            attr_edges_dict = {'color': '#00e629'}
            nd_curr = body[i]
            if isinstance(nd_curr, ast.Assign) or isinstance(nd_curr, ast.AnnAssign) \
                    or isinstance(nd_curr, ast.AugAssign):
                if i == len(body) - 1:
                    return [body[i]]
                else:
                    self.edge_list_cfg.append(((nd_curr, body[i + 1]), attr_edges_dict))
            elif isinstance(nd_curr, ast.Expr):
                exit_nodes = self.get_exit_nodes_EXPR(nd_curr)
                if i == len(body) - 1:
                    return exit_nodes
                else:
                    for exit_node in exit_nodes:
                        self.edge_list_cfg.append(((exit_node, body[i + 1]), attr_edges_dict))
            elif isinstance(nd_curr, ast.FunctionDef):
                exit_nodes = self.get_exit_nodes_FUNCTION(nd_curr)
                if i == len(body) - 1:
                    return exit_nodes
                else:
                    for exit_node in exit_nodes:
                        self.edge_list_cfg.append(((exit_node, body[i + 1]), attr_edges_dict))
            elif isinstance(nd_curr, ast.If):
                exit_nodes = self.get_exit_nodes_IF(nd_curr)
                if i == len(body) - 1:
                    return exit_nodes
                else:
                    break_nodes = []
                    for exit_node in exit_nodes:
                        if not isinstance(exit_node, ast.Break):
                            if isinstance(exit_node, ast.Continue):
                                break_nodes.append(exit_node)
                            else:
                                self.edge_list_cfg.append(((exit_node, body[i + 1]), attr_edges_dict))
                        else:
                            break_nodes.append(exit_node)
                    if len(break_nodes) > 0:
                        return break_nodes
            elif isinstance(nd_curr, ast.While) or isinstance(nd_curr, ast.For):
                exit_nodes = self.get_exit_nodes_WHILE(nd_curr)
                if i == len(body) - 1:
                    return exit_nodes
                else:
                    for exit_node in exit_nodes:
                        self.edge_list_cfg.append(((exit_node, body[i + 1]), attr_edges_dict))
                    attr_edges_dict = attr_edges_dict.copy()
                    attr_edges_dict['label'] = 'skip'
                    attr_edges_dict['color'] = '#ff0039'
                    self.edge_list_cfg.append(((nd_curr, body[i + 1]), attr_edges_dict))
            elif isinstance(nd_curr, ast.Break):
                return [nd_curr]
            elif isinstance(nd_curr, ast.Continue):
                return [nd_curr]
            elif isinstance(nd_curr, ast.Return):
                return [nd_curr]
            elif isinstance(nd_curr, ast.Import) or isinstance(nd_curr, ast.ImportFrom):
                if i == len(body) - 1:
                    return [body[i]]
                else:
                    self.edge_list_cfg.append(((nd_curr, body[i + 1]), attr_edges_dict))

    def get_exit_nodes_EXPR(self, nd: ast.Expr):
        """

        :param nd:
        :return:
        """
        attr_edges_dict = {'color': '#00e629'}
        child = nd.__dict__['value']
        self.edge_list_cfg.append(((nd, child), attr_edges_dict))
        return [child]

    def get_exit_nodes_IF(self, nd: ast.If):
        """

        :param nd:
        :return:
        """
        exit_nodes = []
        attr_edges_dict = {'color': '#00e629'}

        test = nd.__dict__['test']
        self.edge_list_cfg.append(((nd, test), attr_edges_dict))

        body = nd.__dict__['body']
        lst = self.create_CFG(body)
        if isinstance(lst, list):
            exit_nodes = lst
        attr_edges_dict = dict()
        attr_edges_dict['color'] = '#00e629'
        attr_edges_dict['label'] = 'T'
        self.edge_list_cfg.append(((test, body[0]), attr_edges_dict))

        orelse = nd.__dict__['orelse']
        if len(orelse) > 0:
            attr_edges_dict = dict()
            attr_edges_dict['label'] = 'F'
            attr_edges_dict['color'] = '#ff0039'
            self.edge_list_cfg.append(((test, orelse[0]), attr_edges_dict))
            lst = self.create_CFG(orelse)
            if isinstance(lst, list):
                exit_nodes += lst
        return exit_nodes

    def get_exit_nodes_WHILE(self, nd: ast.While or ast.For):
        """

        :param nd:
        :return:
        """
        exit_nodes = []
        attr_edges_dict = {'color': '#00e629'}

        body = nd.__dict__['body']
        self.edge_list_cfg.append(((nd, body[0]), attr_edges_dict))
        lst = self.create_CFG(body)
        if isinstance(lst, list):
            exit_nodes = lst
        for exit_node in exit_nodes:
            if isinstance(exit_node, ast.Break):
                continue
            else:
                self.edge_list_cfg.append(((exit_node, nd), attr_edges_dict.copy()))
        return exit_nodes

    def get_exit_nodes_FUNCTION(self, nd: ast.FunctionDef):
        """

        :param nd:
        """
        exit_nodes = []
        attr_edges_dict = {'color': '#00e629'}

        body = nd.__dict__['body']
        self.edge_list_cfg.append(((nd, body[0]), attr_edges_dict))
        lst = self.create_CFG(body)
        if isinstance(lst, list):
            exit_nodes = lst
        return exit_nodes
