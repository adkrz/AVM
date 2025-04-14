import sys
from enum import Enum
from typing import Dict

# TODO:
# data types
# initial value
# string arrays
# https://en.wikipedia.org/wiki/Recursive_descent_parser

# input_string = "A=-123.5 + test * 2;\nX=3+5+(2-(3+2));"
input_string = ("""
addr arr[2];
addr Z;
Z = arr[3];

function funkcja(byte A, byte B&, addr c[])
begin
A=1;
end

//TODO: type check, up/downcast, expressions, function call check, PUSH larger numbers

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
expr_is_16bit = False


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


class Type(Enum):
    Byte = 1
    Addr = 2

    @property
    def size(self):
        return 1 if self == Type.Byte else 2


def register_variable(name: str, type_: Type, is_array: bool = False, from_global: bool = False):
    if current_context in function_signatures:
        if name in function_signatures[current_context].args:
            return
    global local_variables
    vdef = Variable(type_, is_array=is_array, from_global=from_global)
    if current_context not in local_variables:
        local_variables[current_context] = {name: vdef}
    else:
        if name not in local_variables[current_context]:
            local_variables[current_context][name] = vdef


def gen_load_store_instruction(name: str, load: bool, dry_run=False) -> "Variable":
    offs = 0

    def gen(offset, is_arg, is_16bit):
        instr = "LOAD" if load else "STORE"
        bits = "16" if is_16bit else ""
        origin = "ARG" if is_arg else "LOCAL"
        code = f"{instr}_{origin}{bits} {offset} ; {name}"
        return code

    # Check function arguments
    if current_context in function_signatures and name in function_signatures[current_context].args:
        for k, v in reversed(function_signatures[current_context].args.items()):
            offs += v.type.size
            if k == name:
                if not dry_run:
                    append_code(gen(offs, True, v.is_16bit))
                return v

    if current_context not in local_variables:
        error(f"Current context is empty: {current_context}")

    # Check global variables:
    if current_context and name in local_variables[""]:
        for k, v in local_variables[""].items():
            if k == name:
                v = local_variables[""][name]
                if not dry_run:
                    bits = "16" if v.is_16bit else ""
                    append_code("PUSH_STACK_START")
                    if offs != 0:
                        append_code(f"#{offs}")
                        append_code("ADD16")
                    if load:
                        append_code(f"LOAD_GLOBAL{bits}")
                    else:
                        append_code(f"STORE_GLOBAL{bits}")
                return v
            offs += v.type.size

    # Check local variables
    if name not in local_variables[current_context]:
        error(f"Unknown variable {name}")
    for k, v in local_variables[current_context].items():
        if k == name:
            if not dry_run:
                append_code(gen(offs, False, v.is_16bit))
            return v
        offs += v.type.size


def typeof(name: str) -> Type:
    # Check function arguments
    if current_context in function_signatures and name in function_signatures[current_context].args:
        return function_signatures[current_context].args[name].type

    if current_context not in local_variables:
        error(f"Current context is empty: {current_context}")

    # Check global variables:
    if current_context and name in local_variables[""]:
        return local_variables[""][name].type

    # Check local variables
    if name not in local_variables[current_context]:
        error(f"Unknown variable {name}")
    return local_variables[current_context][name].type


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
    Comma = 283
    Print = 284
    PrintNewLine = 285
    QuotationMark = 286
    String = 287
    Modulo = 288
    Global = 289
    Byte = 290
    Addr = 291


class Variable:
    def __init__(self, type: Type, by_ref: bool = False, is_array: bool = False, from_global: bool = False):
        """
        :param type: In case of array it's type of underlying elements, array itself is addr
        :param by_ref:
        :param is_array:
        :param from_global:
        """
        self.type = type
        self.by_ref = by_ref
        self.is_array = is_array
        self.from_global = from_global

    @property
    def is_16bit(self):
        return self.is_array or self.type.size == 2


class FunctionSignature:
    def __init__(self):
        self.args: Dict[str, Variable] = {}

    def __str__(self):
        def suffix(v: Variable):
            if v.by_ref:
                return "&"
            if v.is_array:
                return "[]"
            return ""

        return "(" + ", ".join(v.type.name + " " + name + suffix(v) for name, v in self.args.items()) + ")"


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
                elif buffer_l == "byte":
                    current = Symbol.Byte
                    return
                elif buffer_l == "addr":
                    current = Symbol.Addr
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


def parse_factor(dry_run=False, expect_16bit=False):
    global expr_is_16bit
    if accept(Symbol.Identifier):
        if accept(Symbol.LBracket):
            var = current_identifier
            var_def = gen_load_store_instruction(var, True, dry_run=dry_run)
            if var_def.is_16bit:
                expr_is_16bit = True
            parse_expression_typed(expect_16bit=True)  # array indexes are 16bit
            expect(Symbol.RBracket)
            element_size = var_def.type.size
            if element_size > 1:
                if not dry_run:
                    append_code(f"PUSH16 #{element_size}")
                    append_code("MUL16")
            if not dry_run:
                append_code("ADD16")
                append_code("LOAD_GLOBAL") if element_size == 1 else append_code("LOAD_GLOBAL16")
        else:
            var_def = gen_load_store_instruction(current_identifier, True, dry_run=dry_run)
            if expect_16bit and not var_def.is_16bit:
                if not dry_run:
                    append_code("EXTEND")
    elif accept(Symbol.Number):
        if current_number > 255:
            expr_is_16bit = True
            if not dry_run:
                append_code(f"PUSH16 #{current_number}")
        else:
            if not dry_run:
                append_code(f"PUSH {current_number}")
    elif accept(Symbol.LParen):
        parse_expression_typed(expect_16bit=expect_16bit)
        expect(Symbol.RParen)
    else:
        error("factor: syntax error")


def parse_logical(dry_run=False, expect_16bit=False):
    parse_factor(dry_run=dry_run, expect_16bit=expect_16bit)
    while current in (Symbol.Equals, Symbol.NotEqual, Symbol.Ge, Symbol.Gt, Symbol.Le, Symbol.Lt):
        v = current
        next_symbol()
        parse_factor(dry_run=dry_run, expect_16bit=expect_16bit)
        if v == Symbol.Equals:
            opcode = "EQ" if not expect_16bit else "EQ16"
        elif v == Symbol.NotEqual:
            opcode = "NE" if not expect_16bit else "NE16"
        elif v == Symbol.Gt:
            opcode = "SWAP\nLESS_OR_EQ" if not expect_16bit else "SWAP16\nLESS_OR_EQ16"
        elif v == Symbol.Ge:
            opcode = "SWAP\nLESS" if not expect_16bit else "SWAP16\nLESS16"
        elif v == Symbol.Lt:
            opcode = "LESS" if not expect_16bit else "LESS16"
        elif v == Symbol.Le:
            opcode = "LESS_OR_EQ" if not expect_16bit else "LESS_OR_EQ16"
        else:
            raise NotImplementedError(current)
        if not dry_run:
            append_code(opcode)


def parse_logical_chain(dry_run=False, expect_16bit=False):
    global condition_counter
    parse_logical(dry_run=dry_run, expect_16bit=expect_16bit)
    has_chain = False
    while current in (Symbol.And, Symbol.Or):
        # TODO: precedence
        if accept(Symbol.Or):
            has_chain = True
            if not dry_run:
                append_code("DUP\nJT" if not expect_16bit else "DUP16\nJT16", newline=False)
                append_code(f" cond{condition_counter}_expr_end")
            parse_logical(dry_run=dry_run, expect_16bit=expect_16bit)
            if not dry_run:
                append_code("OR")
        elif accept(Symbol.And):
            has_chain = True
            if not dry_run:
                append_code("DUP\nJF" if not expect_16bit else "DUP16\nJF16", newline=False)
                append_code(f" cond{condition_counter}_expr_end")
            parse_logical(dry_run=dry_run, expect_16bit=expect_16bit)
            if not dry_run:
                append_code("AND")
    if has_chain:
        if not dry_run:
            append_code(f":cond{condition_counter}_expr_end")
            condition_counter += 1


def parse_term(dry_run=False, expect_16bit=False):
    parse_logical_chain(dry_run=dry_run, expect_16bit=expect_16bit)
    while current in (Symbol.Mult, Symbol.Divide, Symbol.Modulo):
        v = current
        next_symbol()
        parse_logical_chain(dry_run=dry_run, expect_16bit=expect_16bit)
        if v == Symbol.Mult:
            opcode = "MUL" if not expect_16bit else "MUL16"
        elif v == Symbol.Divide:
            opcode = "SWAP\nMUL" if not expect_16bit else "SWAP16\nMUL16"
        elif v == Symbol.Modulo:
            opcode = "SWAP\nMOD" if not expect_16bit else "SWAP16\nMOD16"
        else:
            raise NotImplementedError(current)
        if not dry_run:
            append_code(opcode)


def parse_expression(dry_run=False, expect_16bit=False):
    um = False
    if current == Symbol.Plus or current == Symbol.Minus:
        um = True
        next_symbol()
    parse_term(dry_run=dry_run, expect_16bit=expect_16bit)
    if um and not dry_run:
        append_code("NEG" if not expect_16bit else "NEG16")  # not yet implemented
    while current == Symbol.Plus or current == Symbol.Minus:
        v = current
        next_symbol()
        parse_term()
        if not dry_run:
            if expect_16bit:
                append_code("ADD" if v == Symbol.Plus else "SUB2")
            else:
                append_code("ADD16" if v == Symbol.Plus else "SUB216")


def parse_expression_typed(expect_16bit=False):
    global position
    global line_number
    global condition_counter
    global expr_is_16bit

    expr_is_16bit = False
    position_backup = position
    ln_backup = line_number
    cond_backup = condition_counter

    parse_expression(dry_run=True, expect_16bit=False)

    position = position_backup
    line_number = ln_backup
    condition_counter = cond_backup

    downcast = expr_is_16bit and not expect_16bit

    parse_expression(dry_run=False, expect_16bit=expr_is_16bit)

    if downcast:
        append_code("SWAP\nPOP")


def parse_statement(inside_loop=False, inside_if=False, inside_function=False):
    global if_counter
    global while_counter

    if current in (Symbol.Byte, Symbol.Addr):
        var_type = Type.Byte if current == Symbol.Byte else Type.Addr
        next_symbol()
        expect(Symbol.Identifier)
        var_name = current_identifier

        if accept(Symbol.LBracket):
            register_variable(var_name, var_type, is_array=True)
            append_code("PUSH_NEXT_SP")
            gen_load_store_instruction(var_name, False)
            parse_expression()
            element_size = var_type.size
            if element_size > 1:
                append_code(f"PUSH {element_size}")
                append_code(f"MUL")
            expect(Symbol.RBracket)
            expect(Symbol.Semicolon)
            append_code(f"PUSHN2 ; {var_name} alloc")
        else:
            register_variable(var_name, var_type)
            expect(Symbol.Semicolon)

    elif accept(Symbol.Identifier):
        var = current_identifier
        if accept(Symbol.Becomes):
            parse_expression_typed(expect_16bit=typeof(var).size == 2)
            gen_load_store_instruction(var, False)
            expect(Symbol.Semicolon)
        elif accept(Symbol.LBracket):
            parse_expression_typed(expect_16bit=True)
            element_size = typeof(var).size
            if element_size > 1:
                append_code(f"PUSH16 #{element_size}")
                append_code("MUL16")
            expect(Symbol.RBracket)
            expect(Symbol.Becomes)
            var_type = gen_load_store_instruction(var, True)
            append_code("ADD16")
            parse_expression_typed(expect_16bit=var_type.is_16bit)
            # stack is in wrong order, fix it:
            append_code("ROLL3")  # not yet implemented
            append_code("STORE_GLOBAL")

            expect(Symbol.Semicolon)
    elif accept(Symbol.Global):
        expect(Symbol.Identifier)
        if current_identifier not in local_variables[""]:
            error(f"Unknown global variable {current_identifier}")
        gvar = local_variables[""][current_identifier]
        register_variable(current_identifier, gvar.type, is_array=gvar.is_array, from_global=True)
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
        parse_expression_typed(expect_16bit=False)

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
        parse_expression_typed(expect_16bit=False)
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
                parse_expression_typed(expect_16bit=arg.is_16bit)
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
                append_code(f"POPN {arg.type.size}")
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
            parse_expression_typed(expect_16bit=False)
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
            if current in (Symbol.Byte, Symbol.Addr):
                var_type = Type.Byte if current == Symbol.Byte else Type.Addr
                next_symbol()
                expect(Symbol.Identifier)
                var_name = current_identifier

                if accept(Symbol.LBracket):
                    expect(Symbol.RBracket)
                    arg = Variable(var_type, is_array=True)
                elif accept(Symbol.Reference):
                    arg = Variable(var_type, by_ref=True)
                else:
                    arg = Variable(var_type)
                signature.args[var_name] = arg
            else:
                error("Expected type")

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
            stack_size = var.type.size if not var.is_array else 2
            txt += f"PUSHN {stack_size} ; {var.type.name} {k}\n"
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
