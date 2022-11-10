from src.pl0_code_generator.const import Inst as t, Op as o
from ete3 import Tree

def inst(instruction: t):
    return instruction.value


def op(operation: o):
    return operation.value


class Pl0:

    def __init__(self, abstract_syntax_tree: Tree) -> None:
        self.code = []
        self.ast = abstract_syntax_tree
        self.stck = []

    def generate_instruction(self, inst_name, param1, param2):
        self.code.append([inst_name, param1, param2])

    def generate_code(self):
        pass

    def print_code(self):
        for index, c in enumerate(self.code):
            print(index, "", c[0], c[1], c[2])

    def gen(self, something):
        # dummy method
        pass

    def gen_const(self, const):
        self.generate_instruction(inst(t.lit), 0, const)

    def gen_opr(self, const1, operator: o, const2):
        self.gen_const(const1)
        self.gen_const(const2)
        self.generate_instruction(inst(t.opr), 0, op(operator))

    def gen_if_else(self, cond1, operator: o, cond2, statement_true, statement_false):
        self.gen_opr(cond1, operator, cond2)
        self.generate_instruction(inst(t.jmc), 0, "X")
        self.gen(statement_true)
        self.generate_instruction(inst(t.jmp), 0, "Y")
        self.gen(statement_false)
