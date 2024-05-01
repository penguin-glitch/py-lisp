# This is a mostly functional LISP interpreter written in python, as a first foray into metaprogramming

from typing import ByteString
from numbers import Number
import datetime

# TO DO
# Exception handling
# Primitives (expose the python functions to lisp)
# CURRENT ISSUE: We should only evaluate the part of the if statement that is being run, otherwise if theres a function there we get bad times

class LispError(Exception):
    pass

# Procedures

# Arithmetic Procedures
def arithmetic(func):
    """ Wrapper for arithmetic procedures """
    def wrapper(args):

        processed_args = []
        for arg in args:
            processed_args.append(eval_lisp(arg))
        args = processed_args

        # If there's a float number involved, convert all arguments to float. Otherwise use integers
        float_arithmetic = False
        for arg in args:
            if '.' in str(arg):
                float_arithmetic = True
                break
        
        if float_arithmetic:
            args = [float(arg) for arg in args]
        else:
            args = [int(arg) for arg in args]
        
        x = args[0]
        for arg in args[1:]:
            x = func(x, arg)
        return x
    return wrapper

@arithmetic
def add(x, arg):
    return x + arg

@arithmetic
def subtract(x, arg):
    return x - arg

@arithmetic
def mult(x, arg):
    return x * arg

@arithmetic
def divide(x, arg):
    return x / arg

# Comparison procedures
def comparison(func):
    def wrapper(args):
        processed_args = []
        for arg in args:
            processed_args.append(eval_lisp(arg))
        return func(processed_args[0], processed_args[1])
    return wrapper

@comparison
def gt(a, b):
    return a > b

@comparison
def lt(a, b):
    return a < b

@comparison
def eq(a, b):
    return a == b

@comparison
def gteq(a, b):
    return a >= b

@comparison
def lteq(a, b):
    return a <= b

# Compound conditionals
@comparison
def _and(a, b):
    return eval_lisp(a) and eval_lisp(b)

@comparison
def _or(a, b):
    return eval_lisp(a) or eval_lisp(b)

def _not(cond):
    return not cond[0]

# Other procedures
def create_procedure(base_args: list, lisp_func: str) -> callable:
    """ Returns a new function to be associated with a lisp procedure """

    # DO NOT EXPAND
    def process_args(lisp_func, args):
        processed_func = lisp_func
        for arg in args:
            # This is horrendous but tired brain can't think of a better way to do it
            # Essentially we just want to replace the variable when it's on its own
            # Not when its a part of a larger term
            # Collapse this function for your own sanity
            processed_func = processed_func.replace(' ' + arg[0] + ' ', ' ' + str(arg[1]) + ' ')
            processed_func = processed_func.replace('(' + arg[0] + ' ', '(' + str(arg[1]) + ' ')
            processed_func = processed_func.replace(' ' + arg[0] + ')', ' ' + str(arg[1]) + ')')
            processed_func = processed_func.replace('(' + arg[0] + ')', '(' + str(arg[1]) + ')')

        return processed_func

    def new_procedure(args):
        args = list(zip(base_args, args))
        processed_func = process_args(lisp_func, args)
        return eval_lisp(processed_func)
    return new_procedure
        
def define(exp):
    """ Function/Variable definition """
    try:
        exp = process(descend(exp))
        if is_procedure(exp[1]):
            # Function definition
            callsign = process(descend(exp[1]))
            name = callsign[0]
            args = callsign[1:]
            func = exp[2]
            procedures[name] = create_procedure(args, func)
        else:
            symbols[exp[1]] = eval_lisp(exp[2])
        return exp[2]
    except IndexError:
        return 
    
def _if(args):
    predicate = eval_lisp(args[0])
    consequent = args[1]
    alternative = args[2]

    if predicate:
        return eval_lisp(consequent)
    else:
        return eval_lisp(alternative)


# Memory

symbols = {}
procedures = {'+': add,
              '-': subtract,
              '*': mult,
              '/': divide,
              'if': _if,
              '>': gt,
              '<': lt,
              '=': eq,
              '>=': gteq,
              '<=': lteq,
              'and': _and,
              'or': _or,
              'not': _not}


# Classification Functions

def is_self_evaluating(exp):
    try:
        # Hijack python evaluation
        result = eval(str(exp))
        if isinstance(result, Number) or isinstance(result, ByteString):
            return True
    except (ValueError, SyntaxError, NameError, TypeError):
        pass
    return False
    
def is_variable(exp):
    if exp in symbols.keys():
        return True
    return False

def is_procedure(exp):
    if exp[0] == '(' and exp[-1] == ')':
        return True
    
def is_definition(exp):
    if process(descend(exp))[0] == "define":
        return True


# String processing functions 
    
def eval_brackets(subtext:str) -> str:
    """ Locates bracket pairs and returns a string containing the brackets and the text inside"""

    buffer = []
    for i in range(len(subtext)):
        if subtext[i] == "(":
            buffer.append(i)
        elif subtext[i] == ")":
            if len(buffer) == 1:
                # Done!
                return subtext[buffer[0]:i+1]
            buffer.pop()

def descend(exp):
    try:
        if len(eval_brackets(exp)) == len(exp): # Is the entire expression contained within a bracket?
            return exp[1:-1]
    except TypeError:
        # Crops up when there are no brackets at all in the expression
        pass
    return exp

def process(text):
    """Takes input and splits it up into expressions """
    
    expressions = []
    while text:
        text = text.strip()
        exp = ''
        for i in range(len(text)):
            if text[i] == "(":
                exp = eval_brackets(text[i:])
            elif text[i] != ' ':
                exp += text[i]
                if i != len(text) - 1:
                    continue
            expressions.append(exp)
            try:
                text = text.replace(exp, '', 1)
            except TypeError:
                raise LispError("Bracket not closed")
            break

    return expressions


# Core functions

def apply(proc):
    """ Execution phase """

    proc = process(descend(proc))
    key = proc[0]

    if key in procedures.keys():
        # This is an actual procedure
        args = proc[1:]
        
        return procedures[key](args)
    else:
        # This is another expression in a bracket
        if len(proc) > 1:
            raise LispError("Not evaluable: " + str(proc))
        else:
            return eval_lisp(proc[0])

def eval_lisp(component):
    """ Evaluation stage of the eval-execute loop """

    component = str(component)

    if is_definition(component):
        return define(component)
    elif is_variable(component):
        return symbols[component]
    elif is_procedure(component):
        #print(component)
        return apply(component)
    elif is_self_evaluating(component):
        return eval(str(component))



# Run the interpreter
    
while True:
    expression = input("> ")

    if expression == "quit":
        break

    try:
        for component in process(expression):
            print(eval_lisp(component))
    except (LispError, RecursionError) as e:
        print(e)