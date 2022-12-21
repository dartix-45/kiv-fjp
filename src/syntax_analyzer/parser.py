#  date: 6. 11. 2022
#  author:  Jiri Trefil
#

# vytahnu tokeny, ktere jsem zadefinoval
from ete3 import Tree

from src.lex_analyzer.lexer import tokens
from src.syntax_analyzer.utils import make_node,is_integer,get_integer_node_value

"""
syntakticky parser, pouziva lex pro semanticke vyhodnoceni 
hodne work in progess
lexer provadi lexikalni analyzu a evaluaci hodnoty integeru a boolu
"""

# set priority of operations - plus minus multiply and divide will branch out the tree to the left
# the cfg is ambigous, therefore precende must be defined
precedence = (
    ('nonassoc', 'lt', 'gt', 'le', 'ge', 'equals_equals'),
    ('left', 'plus', 'minus', 'var', 'let'),
    ('left', 'multiply', 'divide'),
    ('right', 'uminus'),
)


# entry point of program, the 'root' of the tree
def p_program(p):
    """program : dekl_list"""
    root = Tree(name='program')
    root.add_child(p[1])
    p[0] = root


# program is just a bunch of declaration statements, this is the core of the grammar
# declartion can produce functions, variables and general expressions, such as function calls or math expressions
def p_dekl_list(p):
    """
    dekl_list : dekl
              | expression semicolon
              | var_modification semicolon
              | var_modification semicolon dekl_list
              | dekl dekl_list
              | block
    """
    n = len(p)
    # block or single declaration
    if n == 2:
        p[0] = make_node('declaration', [p[1]])
    # modification of existing variable
    elif n == 4:
        p[0] = make_node('var_modification_dekl', [p[1], p[3]])
    # expression, modification or declaration list
    elif n == 3:
        # expression or modification
        if p[2] == ";":
            p[0] = make_node('statement', [p[1]])
        # declaration list
        else:
            p[0] = make_node('declaration_list', [p[1], p[2]])


# modification of existing variable
def p_var_modification(p):
    """
    var_modification : id sub expression
                     | id add expression
                     | id mulby expression
                     | id divby expression
                     | id equals expression
    """

    p[0] = make_node("var_modification", [p[1], p[2], p[3]])


# declaration statement
# here we declare variable, constant or a function
def p_dekl(p):
    """
    dekl :   var var_dekl
    | let var_dekl
    | fun_dekl
    """

    if len(p) == 2:
        p[0] = make_node('function_declaration', [p[1]])
    elif len(p) == 3:
        p[0] = make_node('variable_declaration', [p[1], p[2]])


# This function is used to declare a variable.
def p_var_dekl(p):
    """
    var_dekl : id ddot dtype semicolon
    | id ddot dtype equals expression semicolon
    """
    if len(p) == 7:
        p[0] = make_node('var_declaration_expression', [p[1], p[3], p[5]])
    else:
        p[0] = make_node('var_declaration', [p[1], p[3]])


# data type, can be expanded in the future, so far our language accepts only integers and booleans
def p_dtype(p):
    """
    dtype : int_type
    | bool
    """
    p[0] = make_node('data_type', [p[1]])


# general expression - math expressions, variable assignments, functions calls, ...
def p_expression(p):
    """
    expression : expression minus term
    | expression plus term
    | term
    | ternary
    """
    if len(p) == 2:
        p[0] = make_node('expression_term', [p[1]])
    elif p[2] == '+':
        if is_integer(p[1]) and is_integer(p[3]):
            p[0] = make_node('const_expression_term',[get_integer_node_value(p[1])+get_integer_node_value(p[3])])
        else:
            p[0] = make_node('expression_sum', [p[1], p[3]])
    elif p[2] == '-':
        if is_integer(p[1]) and is_integer(p[3]):
            p[0] = make_node('const_expression_term', [get_integer_node_value(p[1]) - get_integer_node_value(p[3])])
        else:
            p[0] = make_node('expression_minus', [p[1], p[3]])

def p_ternary(p):
    """
    ternary : condition question_mark expression ddot expression
    """
    p[0] = make_node("ternary_operator",[p[1],p[3],p[5]])


def p_term(p):
    """
    term : term multiply factor
    |  term divide factor
    | factor
    """
    if len(p) == 2:
        p[0] = make_node('factor', [p[1]])
    elif p[2] == '*':
        #pokud jsou to cisla, zvladnu to vyhodnotit pri prekladu
        if is_integer(p[1]) and is_integer(p[3]):
            p[0] = make_node('const_expression_term',[get_integer_node_value(p[1]) * get_integer_node_value(p[3])])
        #inak nemam tucha, co to je za vysledek
        else:
            p[0] = make_node('expression_multiply', [p[1], p[3]])
    elif p[2] == '/':
        if is_integer(p[1]) and is_integer(p[3]):
            p[0] = make_node('const_expression_term', [get_integer_node_value(p[1]) // get_integer_node_value(p[3])])
        else:
            p[0] = make_node('expression_divide', [p[1], p[3]])


def p_factor(p):
    """
    factor : lparent expression rparent
    | minus expression %prec uminus
    | val
    | call
    """
    if len(p) == 4:
        p[0] = make_node('expression_in_parent', [p[2]])
    elif len(p) == 3:
        if is_integer(p[2]):
            p[0] = make_node('const_expression_term',[-get_integer_node_value(p[2])])
        else:
            p[0] = make_node('unary_minus', [p[1], p[2]])
    elif len(p) == 2:
        p[0] = make_node('factor_expression', [p[1]])


# empty rule, do nothing
def p_empty(p):
    """empty : """
    pass


# function call rule, tree make_node stores operation and value
# value contains id of called function and function arguments
def p_call(p):
    """
    call : id lparent arguments rparent
    """
    p[0] = make_node('function_call', [p[1], p[3]])


# value assignment is integer
#todo when boolean -> true|false
def p_val_num(p):
    """
    val : int
    """
    # vim, ze mi prisel int, castnu to ze stringu na int
    try:
        value = int(p[1])
    except OverflowError:
        print("Out of bounds")
        value = 0
    p[0] = make_node('var_value', [value])


# value assignment is an identifier
def p_val_id(p):
    """
    val : id
    """
    p[0] = make_node('var_value', [ p[1] ])


# rule for function declaration make_node contains operation and val, val contains the relevant information about
# function, such as name, params, body and return type 'fun_dekl : func id lparent params rparent arrow dtype
# comp_block'

def p_fun_dekl(p):
    """
    fun_dekl : func id lparent params rparent arrow dtype comp_block
    """
    p[0] = make_node('function_signature', [p[2], p[4], p[7], p[8]])


# rule for function parameters, ie (<this>)
def p_params(p):
    """
    params : params_var
    | empty
    """
    p[0] = make_node('params', [p[1]])


# function parameter declaration
# initial variable value set to 0
def p_params_var(p):
    """
    params_var : id ddot dtype comma params_var
               | id ddot dtype
    """
    if len(p) == 6:
        p[0] = make_node('parameters_declaration_list', [p[1], p[3], p[5]])
    elif len(p) == 4:
        p[0] = make_node('parameter_declaration', [p[1], p[3]])


# function arguments rule, multiple values separated by comma
def p_arguments(p):
    """
    arguments : val comma arguments
    |   val
    | empty
    """
    if len(p) == 4:
        p[0] = make_node('arguments_list', [p[1], p[3]])
    elif len(p) == 2:
        p[0] = make_node('argument', [p[1]])


# compound block rule, ie {<block>}
def p_comp_block(p):
    """
    comp_block : lcparent block rcparent
    """
    p[0] = make_node('compound_block', [p[2]])


# generic block statement rule
def p_block(p):
    """
    block : comp_block dekl_list
        | loop_block dekl_list
        | cond_block dekl_list
        | let var_dekl dekl_list
        | var var_dekl dekl_list
        | var_modification semicolon dekl_list
        | expression semicolon dekl_list
        | return expression semicolon
        | loop_block
        | cond_block
        | expression semicolon
        | var_modification semicolon
    """
    n = len(p)
    if p[1] == 'return':
        p[0] = make_node('return_statement', [p[2]])
    elif n == 3 and p[2] != ';':
        p[0] = make_node('block', [p[1], p[2]])
    elif n == 4 and p[1] == "var" or p[1] == "let":
        p[0] = make_node('block_var_dekl', [p[1], p[2], p[3]])
    elif n == 4:
        p[0] = make_node('expression', [p[1], p[3]])
    elif n == 2 or (n == 3 and p[2] == ';'):
        p[0] = make_node('block_statement', [p[1]])


# loop statement, for / while cycle
def p_loop_block(p):
    """
    loop_block : for lparent loop_var condition semicolon step semicolon rparent comp_block
    |           while condition comp_block
    |           repeat comp_block while condition semicolon

    """
    if len(p) == 10:
        p[0] = make_node('for_loop_block', [p[3], p[4], p[6], p[9]])
    elif len(p) == 4:
        p[0] = make_node('while_loop_block', [p[2], p[3]])
    elif len(p) == 6:
        p[0] = make_node('repeat_loop_block', [p[2], p[4]])


# condition block, if or if else statement. Switch-case might be added in future
def p_cond_block(p):
    """
    cond_block : if lparent condition rparent comp_block
    |            if lparent condition rparent comp_block else comp_block
    """
    if len(p) == 8:
        p[0] = make_node('if_else_stmt', [p[3], p[5], p[7]])
    elif len(p) == 6:
        p[0] = make_node('if_stmt', [p[3], p[5]])


# loop variable responsible for loop behavior
def p_loop_var(p):
    """
    loop_var : var var_dekl
    | id semicolon
    """
    if p[2] != ";":
        p[0] = make_node('loop_var', [p[1], p[2]])
    else:
        p[0] = make_node('loop_var', [p[1]])


# step in for loop
def p_step(p):
    """
    step : id add int
    | id sub int
    """
    p[0] = make_node('loop_step', [p[1], p[2], p[3]])


# condition statement
def p_condition(p):
    """
    condition : expression relation_operator expression
    """
    p[0] = make_node('condition', [p[1], p[2], p[3]])


# assignment expresion
# either a declaration of variable and assigning a value or assigning value to existing variable
"""
def p_ass_expression(p):
    ''
    ass_exp : var id ddot dtype equals expression
    |   let id ddot dtype equals expression
    | id equals expression
    ''
    if len(p) == 4:
        p[0] = make_node('assign',[p[1],p[3]])
    elif len(p) == 7:
        p[0] = make_node('declaration_assign',[p[2],p[4],p[6]])
"""


# This function is used to parse the relational operators in the input.
def p_relation_operator(p):
    """
    relation_operator : equals_equals
    | lt
    | gt
    | le
    | ge
    | not_equal
    """
    p[0] = make_node('relation_operator', [p[1]])


# todo error handler
def p_error(p):
    if not p:
        print(f"syntax error {p}")

# for lparent loop_var condition semicolon step semicolon rparent
# y = yacc.yacc(debug=True)
# r = y.parse('func a() -> int {if (a<5){return 3;} return 10;}',lexer=lex)
# print(f" {r}")
