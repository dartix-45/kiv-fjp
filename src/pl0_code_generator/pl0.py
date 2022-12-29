#  date: 8. 11. 2022
#  author: Daniel Schnurpfeil
#
from copy import copy

from ete3 import Tree
from src.pl0_code_generator.instructions import Inst, Op
from src.pl0_code_generator.pl0_parent import Pl0Parent
from src.syntax_analyzer.symbol_table import find_real_level, find_entry_in_symbol_table


# > The class Pl0 is a class that represents a PL/0 program
class Pl0(Pl0Parent):

    def __init__(self, abstract_syntax_tree: Tree, symbol_table) -> None:
        """
        The function takes in an abstract syntax tree and initializes the code, ast, and stck attributes.

        :param abstract_syntax_tree: This is the abstract syntax tree that was generated by the parser
        :type abstract_syntax_tree: Tree
        """
        super().__init__(abstract_syntax_tree, symbol_table)

    def generate_instructions(self):
        """
        It generates instructions for the PL/0.
        """
        self.generate_instruction(self.inst(Inst.int), 0, 3)
        self.generate_code(sub_tree=self.clear_tree(self.ast.iter_prepostorder()), symbol_table=self.symbol_table)
        # end of code
        self.generate_instruction(self.inst(Inst.ret), 0, 0)

    # [JT] level stores the current scope, 0 for global, <identifier> for function scope
    # level_numerical current indentation
    def generate_code(self, sub_tree=None, level=0, symbol_table=None):
        # from src.syntax_analyzer.utils import find_real_level

        """
        It generates code for the PL/0 compiler
        :param sub_tree: The current node of the tree that we are generating code for
        :param level: the level of the current node in the tree, defaults to 0 (optional)
        :param symbol_table: a dictionary that maps variable names to their values
        """
        sub_tree = list(sub_tree)
        index = 0
        while index < len(sub_tree):
            #  generates expression_term statements
            if sub_tree[index].name in self.expressions:
                index = self.gen_expression(sub_tree, index, symbol_table=symbol_table, level=level)
            #  generates variable declaration statements
            elif sub_tree[index].name == "var_declaration_expression":
                index, level = self.gen_var_declaration_expression(sub_tree, index, level=level,
                                                                   symbol_table=symbol_table)
            #  generates variable modification statements
            elif sub_tree[index].name in self.var_modifications:
                self.var_modifications[sub_tree[index].name](sub_tree[index].name)

            elif sub_tree[index].name == "var_modification" or sub_tree[index].name == "loop_step":
                index, level = self.gen_var_modification(sub_tree, index, level, symbol_table=symbol_table)
            #  generates if (else) statements
            elif sub_tree[index].name == "if_stmt" or sub_tree[index].name == "if_else_stmt":
                index, level = self.gen_if_else(sub_tree, index, level, symbol_table=symbol_table)
            elif sub_tree[index].name == "function_signature":
                index, level = self.gen_function_signature(sub_tree, index, level=level,
                                                           symbol_table=symbol_table)
            elif sub_tree[index].name == "return_statement":
                index, level = self.generate_code_again(index, level, symbol_table, sub_tree[index].children[0])

            elif sub_tree[index].name == "for_loop_block":
                index, level = self.gen_for_loop_block(sub_tree, index, level=level,
                                                       symbol_table=symbol_table, )
            elif sub_tree[index].name == "while_loop_block":
                index, level = self.gen_while_loop_block(sub_tree, index, level=level,
                                                         symbol_table=symbol_table, )
            elif sub_tree[index].name == "repeat_loop_block":
                index, level = self.gen_repeat_loop_block(sub_tree, index, level=level,
                                                          symbol_table=symbol_table, )

            #  update index
            index += 1

    def gen_while_loop_block(self, sub_tree, index, symbol_table=None, level=0, ):
        """
        It generates the code for a while loop block

        :param sub_tree: the subtree of the AST that represents the while loop
        :param index: the index of the current node in the tree
        :param symbol_table: the symbol table that is passed down from the parent block
        :param level: the level of indentation, defaults to 0 (optional)
        """
        condition = sub_tree[index].children[0]
        body = sub_tree[index].children[1]

        start_address = len(self.code)
        _, index, level = self.gen_condition(condition, index, level, symbol_table=symbol_table)

        x = id("x" + str(level))
        self.generate_instruction(self.inst(Inst.jmc), 0, x)

        index, level = self.generate_code_again(index, level, symbol_table, body)
        for i in self.code:
            if i[2] == x:
                jmc_address = len(self.code)

                i[2] = jmc_address + 1
        self.generate_instruction(self.inst(Inst.jmp), 0, start_address)
        return index, level

    def gen_repeat_loop_block(self, sub_tree, index, symbol_table=None, level=0):
        """
        This function generates the code for a repeat loop block

        :param sub_tree: The subtree of the AST that represents the repeat loop
        :param index: the index of the current node in the tree
        :param symbol_table: the symbol table for the current scope
        :param level: the level of indentation, defaults to 0 (optional)
        """
        condition = sub_tree[index].children[1]
        body = sub_tree[index].children[0]

        start_address = len(self.code)
        index, level = self.generate_code_again(index, level, symbol_table, body)

        _, index, level = self.gen_condition(condition, index, level, symbol_table=symbol_table)
        self.generate_instruction(self.inst(Inst.jmc), 0, len(self.code) + 2)
        self.generate_instruction(self.inst(Inst.jmp), 0, start_address)
        return index, level

    def gen_for_loop_block(self, sub_tree, index, symbol_table=None, level=0):
        """
        It generates the code for a for loop block

        :param sub_tree: The subtree of the AST that represents the loop block
        :param index: the index of the current node in the tree
        :param symbol_table: The symbol table that is being used to store the variables
        :param level: the level of indentation, defaults to 0 (optional)
        """
        loop_var = sub_tree[index].children[0].children[1]
        condition = sub_tree[index].children[1]
        loop_step = sub_tree[index].children[2]
        body = sub_tree[index].children[3]

        index, level = self.generate_code_again(index, level, symbol_table, loop_var)
        start_address = len(self.code)
        _, index, level = self.gen_condition(condition, index, level, symbol_table=symbol_table)

        x = id("x" + str(level))
        self.generate_instruction(self.inst(Inst.jmc), 0, x)

        index, level = self.generate_code_again(index, level, symbol_table, body)
        index, level = self.generate_code_again(index, level, symbol_table, loop_step)
        for i in self.code:
            if i[2] == x:
                jmc_address = len(self.code)

                i[2] = jmc_address + 1
        self.generate_instruction(self.inst(Inst.jmp), 0, start_address)
        return index, level

    def gen_function_signature(self, sub_tree, index, symbol_table=None, level=0):
        """
        This function generates the function signature adn body for a function definition

        :param sub_tree: the subtree of the AST that we're currently working on
        :param index: the index of the current node in the tree
        :param symbol_table: The symbol table that the function is being added to
        :param level: the level of the function in the tree, defaults to 0 (optional)
        """
        old_scope = self.current_scope
        self.curr_func_name = sub_tree[index].children[0].name
        self.current_scope = sub_tree[index].children[0].name
        y = id("y" + str(self.curr_func_name))
        self.generate_instruction(self.inst(Inst.jmp), 0, y)
        self.symbol_table[self.curr_func_name].address = len(self.code)
        func_block = sub_tree[index].children[3].children[0]
        sub_sub_tree = self.clear_tree(func_block.iter_prepostorder())
        index += len(self.clear_tree(sub_tree[index].iter_prepostorder())) - len(sub_sub_tree)

        locals_and_params = {}
        params = {}
        locals = []
        if symbol_table[self.curr_func_name].params is not None:
            params.update(symbol_table[self.curr_func_name].params)
        if symbol_table[self.curr_func_name].locals is not None:
            locals = symbol_table[self.curr_func_name].locals
            # locals_and_params.update({"_indented_blocks": symbol_table[self.curr_func_name].locals})
        # [JT] evaluate function parameters first
        for new_addr, i in enumerate(params.values()):
            i.level = level
        # [JT] number of parameters, needed to calculate the correct address for local variables
        param_count = len(params)
        # [JT] loop through indented blocks inside the function body
        # the core of the loop is basically the same, but it must be done for every block that exists inside the function
        locals_parent_scope_var_count = 0
        for i in range(len(locals)):
            current_block = locals[i]
            for new_addr, j in enumerate(current_block.values()):
                j.level = level
            locals_parent_scope_var_count += len(current_block)

        self.generate_instruction(self.inst(Inst.int), 0, 3)
        for i in range(len(symbol_table[self.curr_func_name].params), 0, -1):
            self.generate_instruction(self.inst(Inst.lod), level, -i)
        self.generate_code(sub_tree=sub_sub_tree, level=level,
                           symbol_table=symbol_table)
        '''
        for local_scope in locals:
            self.generate_code(sub_tree=sub_sub_tree, level=level,
                           symbol_table=local_scope)
        '''
        index += len(sub_sub_tree)
        self.generate_instruction(self.inst(Inst.sto), level, - 1 - (len(symbol_table[self.curr_func_name].params)))
        self.generate_instruction(self.inst(Inst.ret), 0, 0)
        for i in self.code:
            if i[2] == y:
                i[2] = len(self.code)
        # [JT] restore previous scope when we are done with function
        self.current_scope = old_scope
        return index, level

    def gen_var_declaration_expression(self, sub_tree, index, symbol_table=None, level=0):
        """
        It generates a variable declaration expression.

        :param sub_tree: the subtree of the AST that we're currently working on
        :param index: the index of the current node in the tree
        :param symbol_table: the symbol table that the variable is being declared in
        :param level: the level of the current scope, defaults to 0 (optional)
        """
        self.generate_instruction(self.inst(Inst.int), 0, 1)
        name = sub_tree[index].children[0].name
        sub_sub_tree = self.clear_tree(sub_tree[index].children[2].iter_prepostorder())
        if sub_tree[index].children[2].name == "const_expression_term":
            index += 2
        # shifting index to skip duplicates
        # recursive call
        self.generate_code(sub_tree=sub_sub_tree, level=level, symbol_table=symbol_table)
        # [JT] find the current indentation of the identifier @var name
        real_level = find_real_level(sub_tree, index)
        # [JT] find the entry in the symbol table by going bottom up in the stack of scopes in scope defined by
        # @param level
        symbol_table_entry = find_entry_in_symbol_table(symbol_table, self.current_scope, real_level, name)
        self.store_var(symbol_table_entry)
        index += len(sub_sub_tree)
        return index, level

    def gen_condition(self, condition, index, level, symbol_table=None):
        """
        It generates a condition
        for a given index and level

        :param condition: the condition to be generated
        :param index: the index of the current node in the AST
        :param level: the level of indentation
        :param symbol_table: a dictionary of the form {'var_name': 'var_type'}
        """
        index += 2
        index, level = self.generate_code_again(index, level, symbol_table, condition.children[0])
        index, level = self.generate_code_again(index, level, symbol_table, condition.children[2])
        self.cond_expressions[condition.children[1].get_leaf_names()[0]]()
        if condition.name == "condition":
            return condition, index, level
        if condition.name == "compound_condition":
            if condition.children[3].name == "&&":
                and_mark = id("and_mark" + str(level))
                self.generate_instruction(self.inst(Inst.jmc), 0, and_mark)
            elif condition.children[3].name == "||":
                or_mark = id("or_mark" + str(level))
                self.generate_instruction(self.inst(Inst.jmc), 0, or_mark)
            # generates next condition(s)
            _, index, level = self.gen_condition(condition.children[4], index, level, symbol_table)
        #      todo decide where to jump
        return condition, index, level

    def gen_func_call(self, sub_tree, symbol_table=None, level=0):
        """
        It generates the code for a function call

        :param sub_tree: The subtree of the AST that represents the function call
        :param symbol_table: The symbol table that the function is being called in
        :param level: the level of indentation, defaults to 0 (optional)
        """
        i = 0
        func_len = 0

        while i < (len(sub_tree)):
            if sub_tree[i].name == "function_call":
                sub_sub_tree = self.clear_tree(sub_tree[i].iter_prepostorder())
                self.generate_instruction(self.inst(Inst.int), 0, 1)
                f_name = sub_tree[i].children[0].name
                f_args = sub_tree[i].children[1]
                args_len = 0
                while f_args.name == "arguments_list":
                    if f_args.children[0].get_leaf_names()[0] in symbol_table.keys():
                        self.gen_load_symbol(symbol_table[f_args.children[0].get_leaf_names()[0]])
                        args_len += 1
                    else:
                        self.gen_const(f_args.children[0].get_leaf_names()[0])
                        args_len += 1
                    f_args = copy(f_args.children[1])

                if f_args.children[0].get_leaf_names()[0] in symbol_table.keys():
                    self.gen_load_symbol(symbol_table[f_args.children[0].get_leaf_names()[0]])
                    args_len += 1
                elif f_args.children[0].get_leaf_names()[0] != "":
                    self.gen_const(f_args.children[0].get_leaf_names()[0], symbol_table=symbol_table)
                    args_len += 1
                i += len(sub_sub_tree)
                func_len = i
                self.generate_instruction(self.inst(Inst.cal), level, symbol_table[f_name].address)
                if args_len > 0:
                    self.generate_instruction(self.inst(Inst.int), 0, -args_len)
            i += 1
        if func_len > 0:
            return i
        else:
            return None

    def gen_expression(self, sub_tree, index, symbol_table=None, level=0, ):
        """
        It takes a tree, an index, and a symbol table, and returns a string of Python code

        :param level: level
        :param sub_tree: The subtree of the parse tree that we are currently working on
        :param index: the index of the current node in the tree
        :param symbol_table: a dictionary of variables and their values
        """
        real_level = find_real_level(sub_tree, index)
        func_len = self.gen_func_call(sub_tree, symbol_table=symbol_table, level=level)
        if func_len is not None:
            return func_len

        leaf_names = sub_tree[index].get_leaf_names()
        leaves = sub_tree[index].get_leaves()

        if len(leaf_names) > 2:

            if sub_tree[index].children[0].name == "ternary_operator":
                index += 1
                index, level = self.gen_if_else(sub_tree,
                                                index, level, symbol_table=symbol_table)
                return index

            sub_sub_tree = sub_tree[0].get_common_ancestor(leaves[0], leaves[1])
            # shifting index to skip duplicates
            # recursive call
            index = self.gen_expression(sub_tree=self.clear_tree(sub_sub_tree.iter_prepostorder()), index=index,
                                        symbol_table=symbol_table, level=level, )
            for i in range(2, len(leaf_names)):
                parent = sub_tree[0].get_common_ancestor(sub_sub_tree, leaves[i])
                self.expressions[parent.name](leaf_names[i], symbol_table=symbol_table, real_level=real_level)
            index += len(sub_tree)

        elif sub_tree[index].name == "const_expression_term":
            self.expressions[sub_tree[index].name](leaf_names[0], symbol_table=symbol_table)

        elif sub_tree[index].name == "expression_term":
            self.expressions[sub_tree[index].name](leaf_names[0], symbol_table=symbol_table, real_level=real_level)
            if sub_tree[index].children[0].name == "const_expression_term":
                index += len(sub_tree)
        else:
            self.expressions[sub_tree[index].name](leaf_names[0], leaf_names[1], symbol_table=symbol_table,
                                                   real_level=real_level)
            index += 2
        return index

    def gen_var_modification(self, sub_tree, index, level, symbol_table=None):
        """
         This function generates a variable modification statement

        :param sub_tree: The subtree of the AST that we are currently working on
        :param index: the index of the current node in the tree
        :param level: the level of the current scope
        :param symbol_table: a dictionary of the form {'var_name': 'var_type'}
        """
        symbol_name = sub_tree[index].children[0].name
        oper_and_equals = sub_tree[index].children[1]
        # [JT] calculate real level of indentation and find the symbol in symbol table
        real_level = find_real_level(sub_tree, index)
        symbol = find_entry_in_symbol_table(symbol_table, self.current_scope, real_level, symbol_name)

        if sub_tree[index].name == "loop_step":
            self.gen_const(sub_tree[index].children[2].get_leaf_names()[0], symbol_table)
            index += 2
        else:
            index, level = self.generate_code_again(index, level, symbol_table, sub_tree[index].children[2])
        if oper_and_equals.name != "=":
            self.gen_load_symbol(symbol)
        # shifting index to skip duplicates
        # recursive call
        self.generate_code(sub_tree=oper_and_equals, level=level + 1)
        #        self.generate_code(sub_tree=oper_and_equals, level=level)

        index += 1
        self.store_var(symbol)
        return index, level

    def gen_if_else(self, sub_tree, index, level, symbol_table=None):
        """
        It generates the code for an if-else statement

        :param sub_tree: The subtree of the AST that we are currently working on
        :param index: the index of the current node in the tree
        :param level: the level of indentation
        :param symbol_table: The symbol table that is passed down from the parent node
        """
        condition = sub_tree[index].children[0]
        block1 = sub_tree[index].children[1]
        block2 = None
        if sub_tree[index].name == "if_else_stmt" or sub_tree[index].name == "ternary_operator":
            block2 = sub_tree[index].children[2]
        if condition.children[1].get_leaf_names()[0] in self.cond_expressions:
            _, index, level = self.gen_condition(condition, index, level, symbol_table=symbol_table)
            # block 1
            sub_sub_tree = self.clear_tree(block1.iter_prepostorder())
            # shifting index to skip duplicates
            # recursive call
            x = id("x" + str(level))
            self.generate_instruction(self.inst(Inst.jmc), 0, x)
            self.generate_code(sub_tree=sub_sub_tree, level=level + 1, symbol_table=symbol_table)
            #            self.generate_code(sub_tree=sub_sub_tree, level=level, symbol_table=symbol_table)

            index += len(sub_sub_tree)
            for i in self.code:
                if i[2] == x:
                    jmc_address = len(self.code)
                    if block2 is not None:
                        jmc_address += 1
                    i[2] = jmc_address
            if block2 is not None:
                # block 2
                sub_sub_tree = self.clear_tree(block2.iter_prepostorder())
                # shifting index to skip duplicates
                # recursive call
                y = id("y" + str(level))
                self.generate_instruction(self.inst(Inst.jmp), 0, y)
                self.generate_code(sub_tree=sub_sub_tree, level=level + 1, symbol_table=symbol_table)
                #                self.generate_code(sub_tree=sub_sub_tree, level=level, symbol_table=symbol_table)

                index += len(sub_sub_tree)
                for i in self.code:
                    if i[2] == y:
                        i[2] = len(self.code)
        return index, level

    def generate_code_again(self, index, level, symbol_table, sub_tree):
        """
        It generates the code for the given node and its children

        :param index: the index of the current node in the tree
        :param level: the level of the current node in the tree
        :param symbol_table: a dictionary that maps variable names to their values
        :param sub_tree: the subtree of the AST that we are currently generating code for
        """
        sub_sub_tree = self.clear_tree(sub_tree.iter_prepostorder())
        # shifting index to skip duplicates
        # recursive call
        self.generate_code(sub_tree=sub_sub_tree, level=level, symbol_table=symbol_table)

        index += len(sub_sub_tree)
        return index, level
