import sys
from enum import Enum
from typing import Dict

# TODO:
# data types
# string arrays
# https://en.wikipedia.org/wiki/Recursive_descent_parser

# input_string = "A=-123.5 + test * 2;\nX=3+5+(2-(3+2));"
input_string = ("""
X = 5;

function f()
begin
global X;
X = 2;
A = X;
end

""")
position = 0
line_number = 1
current_number = 0
current_identifier = ""
current_string = ""

if_counter = 1
while_counter = 1
condition_counter = 1

codes = {}  # per context
local_variables: Dict[str, Dict[str, "Variable"]] = {}  # per context, then name+details, in order of occurrence
current_context = ""  # empty = global, otherwise in function
string_constants = []


def append_code(c: str, newline=True):
    global codes
    if newline:
        c += "\n"
    if current_context not in codes:
        codes[current_context] = c
    else:
        codes[current_context] += c


def prepend_code(c: str, newline=True):
    global codes
    if newline:
        c += "\n"
    if current_context not in codes:
        codes[current_context] = c
    else:
        codes[current_context] = c + codes[current_context]


def register_variable(name: str, length: int, is_array: bool = False, from_global: bool = False):
    if current_context in function_signatures:
        if name in function_signatures[current_context].args:
            return
    global local_variables
    vdef = Variable(length, is_array=is_array, from_global=from_global)
    if current_context not in local_variables:
        local_variables[current_context] = {name: vdef}
    else:
        if name not in local_variables[current_context]:
            vdef = Variable(length)
            local_variables[current_context][name] = vdef


def gen_load_store_instruction(name: str, load: bool):
    offs = 0

    def gen(offset, is_arg, is_ptr):
        instr = "LOAD" if load else "STORE"
        bits = "16" if is_ptr else ""
        origin = "ARG" if is_arg else "LOCAL"
        code = f"{instr}_{origin}{bits} {offset} ; {name}"
        return code

    # Check function arguments
    if current_context in function_signatures and name in function_signatures[current_context].args:
        for k, v in reversed(function_signatures[current_context].args.items()):
            offs += v.length
            if k == name:
                append_code(gen(offs, True, v.is_array))
                return

    if current_context not in local_variables:
        error(f"Current context is empty: {current_context}")

    # Check global variables:
    if current_context and name in local_variables[""]:
        for k, v in local_variables[""].items():
            if k == name:
                v = local_variables[""][name]
                bits = "16" if v.is_array else ""
                append_code("PUSH_STACK_START")
                if offs != 0:
                    append_code(f"#{offs}")
                    append_code("ADD16")
                # todo: multiply when having variable types
                if load:
                    append_code(f"LOAD_GLOBAL{bits}")
                else:
                    append_code(f"STORE_GLOBAL{bits}")
                return
            offs += v.length


    # Check local variables
    if name not in local_variables[current_context]:
        error(f"Unknown variable {name}")
    for k, v in local_variables[current_context].items():
        if k == name:
            append_code(gen(offs, False, v.is_array))
            return
        offs += v.length


class Symbol(Enum):
    Nothing = -1
    Plus = ord('+')
    Minus = ord('-')
    Mult = ord('*')
    Divide = ord('/')
    Semicolon = ord(';')
    Becomes = ord('=')
    LParen = ord('(')
    RParen = ord(')')
    LBracket = ord('[')
    RBracket = ord(']')
    Number = 256
    Identifier = 259
    EOF = 260
    Equals = 261
    NotEqual = 262
    Gt = 263
    Ge = 264
    Lt = 265
    Le = 266
    # Negate = 267
    If = 268
    Then = 269
    Else = 270
    And = 271
    Or = 272
    Begin = 273
    End = 274
    While = 275
    Do = 276
    Continue = 277
    Break = 278
    Function = 279
    Return = 280
    Call = 281
    Reference = 282
    Comma = 282
    Print = 283
    PrintNewLine = 284
    QuotationMark = 285
    String = 286
    Modulo = 287
    Global = 288


class Variable:
    def __init__(self, length: int, by_ref: bool = False, is_array: bool = False, from_global: bool = False):
        self.length = length
        self.by_ref = by_ref
        self.is_array = is_array
        self.from_global = from_global


class FunctionSignature:
    def __init__(self):
        self.args: Dict[str, Variable] = {}

    def __str__(self):
        return "(" + ", ".join(("&" if v.by_ref else "") + name for name, v in self.args.items()) + ")"


current = Symbol.Nothing

function_signatures: Dict[str, FunctionSignature] = {}


def getchar() -> str:
    global position
    if position < len(input_string):
        ret = input_string[position]
        position += 1
        return ret
    return ""


def rewind():
    global position
    if position > 0:
        position -= 1


def peek() -> str:
    if position < len(input_string):
        return input_string[position]
    return ""


def next_symbol():
    global current
    global current_number
    global current_identifier
    global current_string
    global line_number

    buffer = ""
    buffer_mode = 0  # 1: number 2: identifier 3: string
    # previous_mode = current

    while 1:
        t = getchar()

        if buffer_mode == 1:
            if t.isdigit() or t == '.':
                buffer += t
                continue
            else:
                current_number = int(buffer) if '.' not in buffer else float(buffer)
                if t != "":
                    rewind()
                return
        elif buffer_mode == 3:
            if t != '"' or (t == '"' and buffer and buffer[-1] == '\\'):
                buffer += t
                continue
            else:
                current_string = buffer
                return
        elif buffer_mode == 2:
            if t.isalnum() or t == '_':
                buffer += t
                continue
            else:
                if t != "":
                    rewind()

                buffer_l = buffer.lower()
                if buffer_l == "if":
                    current = Symbol.If
                    return
                elif buffer_l == "then":
                    current = Symbol.Then
                    return
                elif buffer_l == "else":
                    current = Symbol.Else
                    return
                elif buffer_l == "begin":
                    current = Symbol.Begin
                    return
                elif buffer_l == "end":
                    current = Symbol.End
                    return
                elif buffer_l == "while":
                    current = Symbol.While
                    return
                elif buffer_l == "do":
                    current = Symbol.Do
                    return
                elif buffer_l == "continue":
                    current = Symbol.Continue
                    return
                elif buffer_l == "break":
                    current = Symbol.Break
                    return
                elif buffer_l == "function":
                    current = Symbol.Function
                    return
                elif buffer_l == "return":
                    current = Symbol.Return
                    return
                elif buffer_l == "call":
                    current = Symbol.Call
                    return
                elif buffer_l == "print":
                    current = Symbol.Print
                    return
                elif buffer_l == "printnl":
                    current = Symbol.PrintNewLine
                    return
                elif buffer_l == "global":
                    current = Symbol.Global
                    return

                current_identifier = buffer
                return

        if not t:
            current = Symbol.EOF
            return
        elif t in (' ', '\t', '\r'):
            continue
        elif t == '\n':
            line_number += 1
            continue
        elif t.isdigit() or t == '.':  # or (t == '-' and peek().isdigit()):
            current = Symbol.Number
            buffer += t
            buffer_mode = 1
            continue
        elif t.isalnum():
            current = Symbol.Identifier
            buffer += t
            buffer_mode = 2
            continue
        elif t == "\"":
            current = Symbol.String
            buffer_mode = 3
            continue
        elif t == "=":
            if peek() == "=":
                current = Symbol.Equals
                getchar()
            else:
                current = Symbol.Becomes
            return
        elif t == "+":
            current = Symbol.Plus
            return
        elif t == "-":
            current = Symbol.Minus
            return
        elif t == "*":
            current = Symbol.Mult
            return
        elif t == "/" and peek() != "/":  # divide vs comment
            current = Symbol.Divide
            return
        elif t == ";":
            current = Symbol.Semicolon
            return
        elif t == "(":
            current = Symbol.LParen
            return
        elif t == ")":
            current = Symbol.RParen
            return
        elif t == ">":
            if peek() == "=":
                current = Symbol.Ge
                getchar()
            else:
                current = Symbol.Gt
            return
        elif t == "<":
            if peek() == "=":
                current = Symbol.Le
                getchar()
            else:
                current = Symbol.Lt
            return
        elif t == "!":
            if peek() == "=":
                current = Symbol.NotEqual
                getchar()
            # else:
            #    current = Symbol.Negate
            return
        elif t == "&":
            if peek() == "&":
                current = Symbol.And
                getchar()
            else:
                current = Symbol.Reference
            return
        elif t == "|" and peek() == "|":
            current = Symbol.Or
            getchar()
            return
        elif t == "/" and peek() == "/":
            while peek() != '\n':
                getchar()
        elif t == ',':
            current = Symbol.Comma
            return
        elif t == '[':
            current = Symbol.LBracket
            return
        elif t == ']':
            current = Symbol.RBracket
            return
        elif t == '%':
            current = Symbol.Modulo
            return


def accept(t: Symbol) -> bool:
    if t == current:
        next_symbol()
        return True
    return False


def expect(s: Symbol) -> bool:
    if accept(s):
        return True
    error(f"Expected {s}, got {current}")
    return False


def error(what: str):
    print_code()
    print(f"Error in line {line_number}: {what}", file=sys.stderr)
    exit(1)


def parse_factor():
    if accept(Symbol.Identifier):
        if accept(Symbol.LBracket):
            gen_load_store_instruction(current_identifier, True)
            parse_expression()
            expect(Symbol.RBracket)
            append_code("EXTEND")
            append_code("ADD16")  # TODO: multiply if element length>1
            append_code("LOAD_GLOBAL")
        else:
            gen_load_store_instruction(current_identifier, True)
    elif accept(Symbol.Number):
        append_code(f"PUSH {current_number}")
    elif accept(Symbol.LParen):
        parse_expression()
        expect(Symbol.RParen)
    else:
        error("factor: syntax error")


def parse_logical():
    parse_factor()
    while current in (Symbol.Equals, Symbol.NotEqual, Symbol.Ge, Symbol.Gt, Symbol.Le, Symbol.Lt):
        v = current
        next_symbol()
        parse_factor()
        if v == Symbol.Equals:
            opcode = "EQ"
        elif v == Symbol.NotEqual:
            opcode = "NE"
        elif v == Symbol.Gt:
            opcode = "SWAP\nLESS_OR_EQ"
        elif v == Symbol.Ge:
            opcode = "SWAP\nLESS"
        elif v == Symbol.Lt:
            opcode = "LESS"
        elif v == Symbol.Le:
            opcode = "LESS_OR_EQ"
        else:
            raise NotImplementedError(current)
        append_code(opcode)


def parse_logical_chain():
    global condition_counter
    parse_logical()
    has_chain = False
    while current in (Symbol.And, Symbol.Or):
        # TODO: precedence
        if accept(Symbol.Or):
            has_chain = True
            append_code(f"DUP\nJT cond{condition_counter}_expr_end")
            parse_logical()
            append_code("OR")
        elif accept(Symbol.And):
            has_chain = True
            append_code(f"DUP\nJF cond{condition_counter}_expr_end")
            parse_logical()
            append_code("AND")
    if has_chain:
        append_code(f":cond{condition_counter}_expr_end")
        condition_counter += 1


def parse_term():
    parse_logical_chain()
    while current in (Symbol.Mult, Symbol.Divide, Symbol.Modulo):
        v = current
        next_symbol()
        parse_logical_chain()
        if v == Symbol.Mult:
            opcode = "MUL"
        elif v == Symbol.Divide:
            opcode = "SWAP\nMUL"
        elif v == Symbol.Modulo:
            opcode = "SWAP\nMOD"
        else:
            raise NotImplementedError(current)
        append_code(opcode)


def parse_expression():
    um = False
    if current == Symbol.Plus or current == Symbol.Minus:
        um = True
        next_symbol()
    parse_term()
    if um:
        append_code("NEG")  # not yet implemented
    while current == Symbol.Plus or current == Symbol.Minus:
        v = current
        next_symbol()
        parse_term()
        append_code("ADD" if v == Symbol.Plus else "SUB2")


def parse_statement(inside_loop=False, inside_if=False, inside_function=False):
    global if_counter
    global while_counter
    if accept(Symbol.Identifier):
        var = current_identifier
        if accept(Symbol.Becomes):
            if accept(Symbol.LBracket):
                register_variable(var, 2, is_array=True)
                append_code("PUSH_NEXT_SP")
                gen_load_store_instruction(var, False)
                parse_expression()
                expect(Symbol.RBracket)
                expect(Symbol.Semicolon)
                append_code(f"PUSHN2 ; {var} alloc")
            else:
                register_variable(var, 1)
                parse_expression()
                gen_load_store_instruction(var, False)
                expect(Symbol.Semicolon)
        elif accept(Symbol.LBracket):
            parse_expression()
            append_code("EXTEND")
            # TODO: when having array data types, use multiplication if size>1
            expect(Symbol.RBracket)
            expect(Symbol.Becomes)
            gen_load_store_instruction(var, True)
            append_code("ADD16")
            parse_expression()
            # stack is in wrong order, fix it:
            append_code("ROLL3")  # not yet implemented
            append_code("STORE_GLOBAL")

            expect(Symbol.Semicolon)
    elif accept(Symbol.Global):
        expect(Symbol.Identifier)
        register_variable(current_identifier, 1, from_global=True)
        expect(Symbol.Semicolon)

    elif accept(Symbol.Begin):
        cont = True
        while cont:
            parse_statement(inside_loop=inside_loop, inside_if=inside_if, inside_function=inside_function)
            if accept(Symbol.End):
                break
        # expect(Symbol.End)
    elif accept(Symbol.If):
        # TODO: optimize unnecessary jumps if IF without ELSE
        no = if_counter
        if_counter += 1  # increment right away, because we may nest code
        parse_expression()

        append_code(f"JF @if{no}_else")

        inside_if = True

        expect(Symbol.Then)
        parse_statement(inside_loop=inside_loop, inside_if=inside_if, inside_function=inside_function)
        append_code(f"JMP @if{no}_endif")
        append_code(f":if{no}_else")

        if accept(Symbol.Else):
            if not inside_if:
                error("Else outside IF")
            parse_statement(inside_loop=inside_loop, inside_if=inside_if, inside_function=inside_function)

        append_code(f":if{no}_endif")

    elif accept(Symbol.While):
        no = while_counter
        while_counter += 1
        append_code(f":while{no}_begin")
        parse_expression()
        append_code(f"JF @while{no}_endwhile")

        expect(Symbol.Do)

        parse_statement(inside_loop=True, inside_if=inside_if, inside_function=inside_function)

        append_code(f":while{no}_endwhile")

    elif accept(Symbol.Break):
        expect(Symbol.Semicolon)
        if not inside_loop:
            error("Break outside loop")
        no = while_counter
        append_code(f"JMP @while{no}_endwhile")

    elif accept(Symbol.Continue):
        expect(Symbol.Semicolon)
        if not inside_loop:
            error("Continue outside loop")
        no = while_counter
        append_code(f"JMP @while{no}_begin")

    elif accept(Symbol.Call):
        expect(Symbol.Identifier)
        func = current_identifier
        if func not in function_signatures:
            error(f"Unknown function {func}")
        signature = function_signatures[func]

        expect(Symbol.LParen)

        append_code(";" + func + str(signature))

        refs_mapping = {}
        for i, arg in enumerate(signature.args.values()):
            if i > 0:
                expect(Symbol.Comma)
            if not arg.by_ref:
                parse_expression()
            else:
                expect(Symbol.Identifier)
                gen_load_store_instruction(current_identifier, True)
                refs_mapping[arg] = current_identifier

        expect(Symbol.RParen)

        expect(Symbol.Semicolon)
        append_code(f"CALL @function_{func}")

        append_code("; stack cleanup")
        for arg in reversed(signature.args.values()):
            if not arg.by_ref:
                append_code(f"POPN {arg.length}")
            else:
                gen_load_store_instruction(refs_mapping[arg], False)

    elif accept(Symbol.Return):
        if not inside_function:
            error("Return outside function")
        append_code("RET")
        expect(Symbol.Semicolon)

    elif accept(Symbol.Print):
        if accept(Symbol.String):
            string_constants.append(current_string)
            append_code(f"PUSH16 @string_{len(string_constants)}")
            append_code("SYSCALL Std.PrintString")
        else:
            parse_expression()
            append_code("SYSCALL Std.PrintInt")
        expect(Symbol.Semicolon)

    elif accept(Symbol.PrintNewLine):
        append_code("SYSCALL Std.PrintNewLine")
        expect(Symbol.Semicolon)

    else:
        error("parse statement")


def parse_block(inside_function=False):
    global current_context
    global function_signatures

    if accept(Symbol.EOF):
        return

    elif accept(Symbol.Function):
        expect(Symbol.Identifier)
        old_ctx = current_context
        current_context = current_identifier

        signature = FunctionSignature()
        function_signatures[current_context] = signature

        expect(Symbol.LParen)

        while not accept(Symbol.RParen):
            if signature.args:
                expect(Symbol.Comma)
            if accept(Symbol.Identifier):
                if accept(Symbol.LBracket):
                    expect(Symbol.RBracket)
                    arg = Variable(2, by_ref=False, is_array=True)
                else:
                    arg = Variable(1, by_ref=False)
                signature.args[current_identifier] = arg
            elif accept(Symbol.Reference):
                next_symbol()
                arg = Variable(1, by_ref=True)
                signature.args[current_identifier] = arg

        if accept(Symbol.Semicolon):
            # just a declaration
            pass
        else:
            # definition
            parse_block(True)
            append_code("RET")
            generate_preamble()
            prepend_code(f":function_{current_context}\n;{signature}")
        current_context = old_ctx
    else:
        parse_statement(inside_function=inside_function)


def generate_preamble():
    txt = ""
    if current_context not in local_variables:
        return
    for k, var in local_variables[current_context].items():
        if not var.from_global:
            txt += f"PUSHN {var.length} ; {k}\n"
    # todo: optimize into one big block
    # todo: initial value instead of just push
    prepend_code(txt, False)


def print_code():
    # "main" must be printed first to not execute functions
    if "" in codes:
        print(codes[""])
    for ctx, code in codes.items():
        if ctx:
            print(code)
    for i, stc in enumerate(string_constants):
        print(f":string_{i + 1}")
        print(f"\"{stc}\"")


if __name__ == '__main__':
    next_symbol()
    while not accept(Symbol.EOF):
        parse_block()
    current_context = ""
    append_code("HALT")
    generate_preamble()
    print_code()
    # expect(Symbol.Semicolon)
