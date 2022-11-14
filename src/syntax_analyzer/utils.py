#  date: 11. 11. 2022
#  author: Daniel Schnurpfeil
#

from ete3 import Tree

from src.pl0_code_generator import SymbolRecord


def make_node(node_name: str, children=None) -> Tree:
    """
    It takes a node name and a list of children, and returns a tree

    :param node_name: The name of the node
    :type node_name: str
    :param children: A list of children to add to the node
    :return: A tree with the name of the node and the children
    """
    ast = Tree(name=node_name)

    if children is None:
        return ast
    for i in children:
        if i.__class__.__name__ == 'TreeNode':
            ast.add_child(child=i)
        else:
            ast.add_child(name=i)
    return ast


def generate_table_of_symbols(symbol_table, level=0, symbols=None):
    """
        It generates a table of symbols
        """
    symbols = symbols
    level = level
    index = 0
    address = 3
    while index < len(symbols):
        ancestor = symbols[index].get_ancestors()[0]
        if ancestor.name == "function_signature":
            if symbols[index].name in symbol_table.keys():
                raise Exception("Duplicate symbol:", symbols[index].name, "in", symbol_table.keys())
            params = {}
            for index, i in enumerate(symbols[index].get_sisters()[0].children):
                id_and_type = i.get_leaf_names()
                if id_and_type[0] in params.keys():
                    raise Exception("Duplicate symbol:", id_and_type[0], "in", params.keys())
                params[id_and_type[0]] = (SymbolRecord(id_and_type[0], id_and_type[1], param=True, level=level,
                                                       address=address))
                address += 1
            symbol_table[symbols[index].name] = (
                SymbolRecord(symbols[index].name, "func", params=params, level=level,
                             address=address,
                             return_type=symbols[index].get_sisters()[1].get_leaf_names()[0]))
            address += 1
            func_body = symbols[index].get_sisters()[2].get_leaves()
            # shifting index to skip duplicates
            index += len(func_body)
            # recursive call
            generate_table_of_symbols(symbol_table, level=level + 1, symbols=func_body)
        if ancestor.name == "var_declaration_expression":
            if symbols[index].name in symbol_table.keys():
                raise Exception("Duplicate symbol:", symbols[index].name, "in", symbol_table.keys())
            symbol_table[symbols[index].name] = (SymbolRecord(symbols[index].name,
                                                              symbol_type=
                                                              symbols[index].get_sisters()[0].children[0].name,
                                                              level=level,
                                                              address=address))
            address += 1
            if ancestor.get_sisters()[0].name == "let":
                symbol_table[symbols[index].name].const = True
        index += 1
