#  date: 8. 11. 2022
#  author: Daniel Schnurpfeil
#

from ete3 import Tree

from src.pl0_code_generator.const import Inst as t, Op as o, reserved, types, SymbolRecord
from src.pl0_code_generator.pl0_utils import inst, op


# > The class Pl0 is a class that represents a PL/0 program
class Pl0:

    def __init__(self, abstract_syntax_tree: Tree) -> None:
        """
        The function takes in an abstract syntax tree and initializes the code, ast, and stck attributes.

        :param abstract_syntax_tree: This is the abstract syntax tree that was generated by the parser
        :type abstract_syntax_tree: Tree
        """
        self.code = []
        self.ast = abstract_syntax_tree
        self.stck = []
        self.symbol_table = []
        self.generate_table_of_symbols()

    def generate_instruction(self, inst_name, param1, param2):
        """
        It appends a list of three elements to the list called code

        :param inst_name: The name of the instruction
        :param param1: the first parameter of the instruction
        :param param2: the value of the second parameter
        """
        self.code.append([inst_name, param1, param2])

    def print_code(self):
        """
        It prints the code of the program
        """
        for index, c in enumerate(self.code):
            print(index, "", c[0], c[1], c[2])

    def return_code(self) -> str:
        """
        This function returns a string of the code in the format of "index opcode operand1 operand2"
        :return: The return_code method returns a string of the code.
        """
        code_string = ""
        for index, c in enumerate(self.code):
            code_string += (str(index) + " " + c[0] + " " + c[1] + " " + c[2] + "\n")
        return code_string

    def generate_table_of_symbols(self):
        """
        It generates a table of symbols
        """
        symbols = self.ast.get_leaves()
        for leaf in symbols:
            ancestor = leaf.get_ancestors()[0]
            if ancestor.name == "var_declaration_expression":
                self.symbol_table.append(SymbolRecord(leaf.name, leaf.get_sisters()[0].children[0].name))
                if ancestor.get_sisters()[0].name == "let":
                    self.symbol_table[-1].const = True

        [i.__str__() for i in self.symbol_table]

    def gen_const(self, const):
        """
        It generates a constant

        :param const: The constant to be generated
        """
        self.generate_instruction(inst(t.lit), 0, const)

    def gen_opr(self, const1, operator: o, const2):
        """
        It generates instructions for the operation of two constants

        :param const1: The first constant to be used in the operation
        :param operator: o = enum('+', '-', '*', '/', '<', '>', '=', '<=', '>=', '<>', 'and', 'or', 'not', 'neg')
        :type operator: o
        :param const2: The second constant to be used in the operation
        """
        self.gen_const(const1)
        self.gen_const(const2)
        self.generate_instruction(inst(t.opr), 0, op(operator))

    def gen(self, something):
        # dummy method
        pass

    def generate_code(self):
        for i in self.ast.iter_prepostorder():
            if not i[0]:
                print(i[1].name)
                if i[1].name in self.symbol_table:
                    pass

    def gen_if_else(self, cond1, operator: o, cond2, statement_true, statement_false):
        self.gen_opr(cond1, operator, cond2)
        self.generate_instruction(inst(t.jmc), 0, "X")
        self.gen(statement_true)
        self.generate_instruction(inst(t.jmp), 0, "Y")
        self.gen(statement_false)
