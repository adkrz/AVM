from enum import Enum
from typing import Dict, Sequence, Optional

from lexer import Lexer, Symbol
from optimizer import optimize

"""
TODO:
optimize functions with single return value, use them directly in expressions
"""


class Type(Enum):
    Byte = 1
    Addr = 2
    Struct = 3

    @property
    def size(self):
        if self == Type.Struct:
            raise NotImplementedError("Use specific method to calc struct sizes")
        return 1 if self == Type.Byte else 2


class StructDefinition:
    def __init__(self, name):
        self._name = name
        self.members: Dict[str, Variable] = {}

    @property
    def name(self):
        return self._name

    @property
    def stack_size(self) -> int:
        return self.member_offset("")

    def member_offset(self, member_name: str) -> int:
        offset = 0
        for name, m in self.members.items():
            if name == member_name:
                return offset
            offset += m.stack_size
        return offset


class Variable:
    def __init__(self, type_: Type, by_ref: bool = False, is_array: bool = False, from_global: bool = False, struct_def: Optional[StructDefinition] = None):
        """
        :param type_: In case of array its type of underlying elements, array itself is addr
        :param by_ref:
        :param is_array:
        :param from_global:
        """
        self.type = type_
        self.by_ref = by_ref
        self.is_array = is_array
        self.from_global = from_global
        self.struct_def = struct_def
        self.array_fixed_size = 0  # for stack size
        self.array_fixed_len = 0  # only for initializer lists
        self.is_arg = False

    @property
    def is_16bit(self):
        return (self.is_array or (self.type != Type.Struct and self.type.size == 2)
                or (self.struct_def and self.is_arg))  # structs are passed as ptr

    @property
    def stack_size(self):
        s = self.stack_size_single_element
        if self.array_fixed_size > 1:
            s *= self.array_fixed_size
        return s

    @property
    def stack_size_single_element(self):
        if self.type == Type.Struct:
            if self.is_arg:
                return 2  # structs are passed as ptr
            s = self.struct_def.stack_size
        else:
            s = 2 if self.is_16bit else 1
        return s


class Constant:
    def __init__(self, type_: Type, value: int):
        self.type = type_
        self.value = value

    @property
    def is_16bit(self):
        return self.type.size == 2


class FunctionSignature:
    RETURN_VALUE_NAME = "@ret"

    def __init__(self):
        self.args: Dict[str, Variable] = {}

    @property
    def true_args(self) -> Sequence[Variable]:
        """ Arguments, except special return value argument """
        for k, v in self.args.items():
            if k != self.RETURN_VALUE_NAME:
                yield v

    @property
    def return_value(self) -> Optional[Variable]:
        if self.RETURN_VALUE_NAME in self.args:
            return self.args[self.RETURN_VALUE_NAME]
        return None

    def __str__(self):
        def suffix(v: Variable):
            if v.by_ref:
                return "&"
            if v.is_array:
                return "[]"
            return ""

        return "(" + ", ".join(v.type.name + " " + name + suffix(v) for name, v in self.args.items()) + ")"


class ExprContext:
    """
    Expression context: if we expect 16bit, what type we really get, is it a dry run (no code generation yet)
    """
    def __init__(self, parent_parser: "Parser", expect_16bit=False):
        self.parent_parser = parent_parser
        self.expr_is16bit = False
        self.dry_run = False
        self.expect_16bit = expect_16bit
        # Some expressions are simple like x[0], while 1 etc
        self.is_simple_constant = True
        self.simple_value = 0

    def clone_with_same_buffer(self) -> "ExprContext":
        c = ExprContext(self.parent_parser, self.expect_16bit)
        c.expr_is16bit = self.expr_is16bit
        c.dry_run = self.dry_run
        return c

    def append_code(self, data, newline=True):
        if not self.dry_run:
            self.parent_parser._append_code(data, newline)


class Parser:
    def __init__(self, input_string: str):
        self._lex = Lexer(input_string)

        self._if_counter = 1
        self._while_counter = 1
        self._condition_counter = 1
        self._codes = {}  # per context
        self._local_variables: Dict[
            str, Dict[str, "Variable"]] = {}  # per context, then name+details, in order of occurrence
        self._constants: Dict[
            str, Dict[str, "Constant"]] = {}  # per context, then name+details, in order of occurrence
        self._current_context = ""  # empty = global, otherwise in function
        self._string_constants = []

        self._function_signatures: Dict[str, FunctionSignature] = {}
        self._struct_definitions: Dict[str, "StructDefinition"] = {}

    def _create_ec(self) -> ExprContext:
        return ExprContext(self)

    def _append_code(self, c: str, newline=True):
        if newline:
            c += "\n"
        if self._current_context not in self._codes:
            self._codes[self._current_context] = c
        else:
            self._codes[self._current_context] += c

    def _prepend_code(self, c: str, newline=True):
        if newline:
            c += "\n"
        if self._current_context not in self._codes:
            self._codes[self._current_context] = c
        else:
            self._codes[self._current_context] = c + self._codes[self._current_context]

    def _register_variable(self, name: str, type_: Type, is_array: bool = False, from_global: bool = False, struct_def: Optional[StructDefinition] = None) -> Variable:
        if self._current_context in self._function_signatures:
            if name in self._function_signatures[self._current_context].args:
                return self._function_signatures[self._current_context].args[name]
        vdef = Variable(type_, is_array=is_array, from_global=from_global, struct_def=struct_def)
        if self._current_context not in self._local_variables:
            self._local_variables[self._current_context] = {name: vdef}
        else:
            if name not in self._local_variables[self._current_context]:
                self._local_variables[self._current_context][name] = vdef
        return vdef

    def _register_constant(self, name: str, type_: Type, value: int) -> Constant:
        cdef = Constant(type_, value)
        if self._current_context not in self._constants:
            self._constants[self._current_context] = {name: cdef}
        else:
            if name not in self._constants[self._current_context]:
                self._constants[self._current_context][name] = cdef
        return cdef

    def _gen_load_store_instruction(self, name: str, load: bool, context: ExprContext) -> "Variable":

        def gen(offset, is_arg, is_16bit):
            instr = "LOAD" if load else "STORE"
            bbits = "16" if is_16bit else ""
            origin = "ARG" if is_arg else "LOCAL"
            code = f"{instr}_{origin}{bbits} {offset} ; {name}"
            return code

        var = self._get_variable(name)
        offs = self._offsetof(name)

        if var.is_arg:
            context.append_code(gen(offs, True, var.is_16bit))
        elif var.from_global:
            bits = "16" if var.is_16bit else ""
            context.append_code("PUSH_STACK_START")
            if offs != 0:
                context.append_code(f"PUSH16 #{offs}")
                context.append_code("ADD16")
            if load:
                context.append_code(f"LOAD_GLOBAL{bits}")
            else:
                context.append_code(f"STORE_GLOBAL{bits}")
        else:
            context.append_code(gen(offs, False, var.is_16bit))

        return var

    def _get_variable(self, name: str) -> Variable:
        # Check function arguments
        if (self._current_context in self._function_signatures and name
                in self._function_signatures[self._current_context].args):
            return self._function_signatures[self._current_context].args[name]

        if self._current_context not in self._local_variables:
            self._error(f"Current context is empty: {self._current_context}, unknown variable {name}")

        # Check local variables, this includes global declarations
        if name not in self._local_variables[self._current_context]:
            self._error(f"Unknown variable {name}")
        return self._local_variables[self._current_context][name]

    def _get_constant(self, name: str) -> Optional[Constant]:
        # Local context
        if self._current_context in self._constants:
            if name in self._constants[self._current_context]:
                return self._constants[self._current_context][name]
        # global context
        if self._current_context != "" and "" in self._constants:
            if name in self._constants[""]:
                return self._constants[""][name]
        return None

    def _offsetof(self, name: str) -> int:
        offs = 0
        # Check function arguments
        if self._current_context in self._function_signatures and name in self._function_signatures[self._current_context].args:
            for k, v in reversed(self._function_signatures[self._current_context].args.items()):
                offs += v.stack_size
                if k == name:
                    return offs

        # Check global variables:
        if self._current_context and "" in self._local_variables and name in self._local_variables[""]:
            for k, v in self._local_variables[""].items():
                if k == name:
                    # v = self._local_variables[""][name]
                    return offs
                offs += v.stack_size

        # Check local variables
        if name not in self._local_variables[self._current_context]:
            self._error(f"Unknown variable {name}")
        for k, v in self._local_variables[self._current_context].items():
            if v.from_global:
                continue
            if k == name:
                return offs
            offs += v.stack_size

    def _accept(self, t: Symbol) -> bool:
        if t == self._lex.current:
            self._lex.next_symbol()
            return True
        return False

    def _expect(self, s: Symbol) -> bool:
        if self._accept(s):
            return True
        self._error(f"Expected {s}, got {self._lex.current}")
        return False

    def _error(self, what: str):
        self.print_code()
        raise Exception(f"Error in line {self._lex.line_number}: {what}")

    def _gen_array_initialization(self, context: ExprContext, new_var_name: str, new_var_type: Optional[Type] = None, struct_def=None) -> Variable:
        vtype = Type.Struct if struct_def else new_var_type
        vdef = self._register_variable(new_var_name, vtype, is_array=True, struct_def=struct_def)

        if self._accept(Symbol.RBracket):
            if self._accept(Symbol.Becomes):
                if self._accept(Symbol.LCurly):
                    # initializer list
                    context.append_code("PUSH_NEXT_SP")
                    context.append_code("PUSH16 #2")
                    context.append_code("SUB216")
                    self._gen_load_store_instruction(new_var_name, False, context)
                    is_16bit = vdef.type.size == 2  # type of element, not of array variable
                    size = 0
                    while 1:
                        if size > 0:
                            self._expect(Symbol.Comma)
                        self._expect(Symbol.Number)
                        size += 1
                        context.append_code(f"PUSH {self._lex.current_number}" if not is_16bit else f"PUSH16 #{self._lex.current_number}")
                        if self._accept(Symbol.RCurly):
                            break
                        vdef.array_fixed_len = size
                else:
                    # this is a raw pointer, no memory reservation, but read address
                    self._parse_expression_typed(expect_16bit=True)
                    self._gen_load_store_instruction(new_var_name, False, context)
            return vdef

        context.append_code("PUSH_NEXT_SP")
        # PUSH_NEXT_SP actually pushes SP+addressSize, so move back:
        context.append_code("PUSH16 #2")
        context.append_code("SUB216")
        self._gen_load_store_instruction(new_var_name, False, context)
        self._parse_expression_typed(expect_16bit=False)  # size of array
        element_size = new_var_type.size if new_var_type else struct_def.stack_size
        if element_size > 1:
            # TODO: array size limitation - no 16 bit version of PUSHN2
            context.append_code(f"PUSH {element_size}")
            context.append_code(f"MUL")
        self._expect(Symbol.RBracket)
        context.append_code(f"PUSHN2 ; {new_var_name} alloc")
        return vdef

    def _gen_address_of_str(self, string_constant: str, context: ExprContext):
        if string_constant not in self._string_constants:
            self._string_constants.append(string_constant)
            index = len(self._string_constants)
        else:
            index = self._string_constants.index(self._lex.current_string) + 1
        context.append_code(f"PUSH16 @string_{index}")

    def _gen_address_of_variable(self, var_name, context: ExprContext):
        var_def = self._get_variable(var_name)
        if var_def.is_array:
            self._gen_load_store_instruction(var_name, True, context)
        elif var_def.from_global:
            context.append_code("PUSH_STACK_START")
            offset = self._offsetof(var_name)
            if offset > 0:
                context.append_code(f"PUSH16 #{offset}")
                context.append_code("ADD16")
        elif var_def.is_arg:
            context.append_code("PUSH_REG 2")
            context.append_code(f"PUSH16 #{self._offsetof(var_name)}")
            context.append_code("SUB16")
            context.append_code("PUSH16 #2")  # saved registers
            context.append_code("SUB16")
        else:
            context.append_code("PUSH_REG 2")
            context.append_code(f"PUSH16 #{self._offsetof(var_name)}")
            context.append_code("ADD16")

    def _parse_intrinsic(self, function_name, context: ExprContext, expected_return):
        #self._expect(Symbol.LParen)
        if function_name == "sizeof":
            if self._accept(Symbol.Byte):
                context.append_code(f"PUSH {Type.Byte.size}")
            elif self._accept(Symbol.Addr):
                context.append_code(f"PUSH {Type.Addr.size}")
            else:
                self._expect(Symbol.Identifier)
                if self._lex.current_identifier in self._struct_definitions:
                    context.append_code(f"PUSH {self._struct_definitions[self._lex.current_identifier].stack_size}")
                else:
                    self._error(f"Unknown data type {self._lex.current_identifier}")
        elif function_name == "length":
            self._expect(Symbol.Identifier)
            var = self._get_variable(self._lex.current_identifier)
            if not var.is_array:
                self._error(f"Variable {self._lex.current_identifier} is not an array")
            size = var.array_fixed_len if var.array_fixed_len > 0 else var.array_fixed_size
            if size <= 255:
                context.append_code(f"PUSH {size}")
            else:
                context.append_code(f"PUSH16 #{size}")
                context.expr_is16bit = True
        elif function_name == "addressof":
            context.expr_is16bit = True
            if self._accept(Symbol.String):
                self._gen_address_of_str(self._lex.current_string, context)
            else:
                self._expect(Symbol.Identifier)
                self._gen_address_of_variable(self._lex.current_identifier, context)
        elif function_name == "pred":
            self._parse_sum(context)
            context.append_code("DEC") if not context.expr_is16bit else context.append_code("DEC16")
        elif function_name == "succ":
            self._parse_sum(context)
            context.append_code("INC") if not context.expr_is16bit else context.append_code("INC16")
        elif function_name == "readkey":
            context.append_code("SYSCALL Std.ReadKey")
        elif function_name == "getrandomnumber":
            self._parse_expression_typed(expect_16bit=False)
            self._expect(Symbol.Comma)
            self._parse_expression_typed(expect_16bit=False)
            context.append_code("SYSCALL Std.GetRandomNumber")
        elif function_name == "consoleclear":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            context.append_code("SYSCALL Std.ConsoleClear")
        elif function_name == "showconsolecursor":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            self._parse_expression_typed(expect_16bit=False)
            context.append_code("SYSCALL Std.ShowConsoleCursor")
        elif function_name == "setconsolecursorposition":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            self._parse_expression_typed(expect_16bit=False)
            self._expect(Symbol.Comma)
            self._parse_expression_typed(expect_16bit=False)
            context.append_code("SYSCALL Std.SetConsoleCursorPosition")
        elif function_name == "setconsolecolors":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            self._parse_expression_typed(expect_16bit=False)
            self._expect(Symbol.Comma)
            self._parse_expression_typed(expect_16bit=False)
            context.append_code("SYSCALL Std.SetConsoleColors")
        elif function_name == "sleep":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            self._parse_expression_typed(expect_16bit=True)
            context.append_code("SYSCALL Std.Sleep")
        elif function_name == "readstring":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            self._parse_expression_typed(expect_16bit=True)
            self._expect(Symbol.Comma)
            self._parse_expression_typed(expect_16bit=False)
            context.append_code("SYSCALL Std.ReadString")
        else:
            self._error(f"Unknown function {function_name}")
        self._expect(Symbol.RParen)

    def _parse_factor(self, context: ExprContext):
        if self._accept(Symbol.Hash):
            context.expr_is16bit = True
            self._expect(Symbol.Number)
            context.append_code(f"PUSH16 #{self._lex.current_number}")
            if context.is_simple_constant:  # is STILL simple constant
                context.simple_value = self._lex.current_number
        elif self._accept(Symbol.Identifier):
            context.is_simple_constant = False
            var = self._lex.current_identifier

            if self._accept(Symbol.LParen):
                # Intrinsics that return value
                self._parse_intrinsic(var, context, expected_return=True)
                return

            constant = self._get_constant(var)
            if constant is not None:
                is16 = constant.is_16bit or context.expect_16bit
                context.append_code(f"PUSH {constant.value}" if not is16 else f"PUSH16 #{constant.value}")
                if context.is_simple_constant:  # is STILL simple constant
                    context.simple_value = constant.value
                if constant.is_16bit:
                    context.expr_is16bit = True
                return

            var_def = self._get_variable(var)

            if var_def.struct_def:
                last_var_in_chain = self._generate_struct_address(var_def, var, context)
                context.append_code("LOAD_GLOBAL") if not last_var_in_chain.is_16bit else context.append_code("LOAD_GLOBAL16")
                context.expr_is16bit = last_var_in_chain.is_16bit
                if not last_var_in_chain.is_16bit and context.expect_16bit:
                    context.append_code("EXTEND")
                return

            if self._accept(Symbol.LBracket):
                var_def = self._gen_load_store_instruction(var, True, context)
                if not var_def.is_array:
                    self._error(f"Variable {var} is not an array!")
                element_size = var_def.type.size
                if element_size == 2:
                    context.expr_is16bit = True
                if self._accept(Symbol.RBracket):
                    # arr[] is the same as arr[0]
                    context.append_code("LOAD_GLOBAL") if element_size == 1 else context.append_code("LOAD_GLOBAL16")
                else:
                    new_context = context.clone_with_same_buffer()
                    new_context.expect_16bit = True   # array indexes are 16bit
                    self._parse_sum(new_context)
                    self._expect(Symbol.RBracket)
                    if element_size > 1:
                        context.expr_is16bit = True
                        context.append_code(f"PUSH16 #{element_size}")
                        context.append_code("MUL16")
                    context.append_code("ADD16")
                    context.append_code("LOAD_GLOBAL") if element_size == 1 else context.append_code("LOAD_GLOBAL16")
                if element_size == 1 and context.expect_16bit:
                    context.append_code("EXTEND")
            else:
                var_def = self._gen_load_store_instruction(var, True, context)
                if var_def.is_16bit:
                    context.expr_is16bit = True
                if context.expect_16bit and not var_def.is_16bit:
                    context.append_code("EXTEND")
                    context.expr_is16bit = True
        elif self._accept(Symbol.Number):
            if self._lex.current_number > 255 or context.expect_16bit or context.expr_is16bit:
                context.expr_is16bit = True
                context.append_code(f"PUSH16 #{self._lex.current_number}")
            else:
                context.append_code(f"PUSH {self._lex.current_number}")
            context.simple_value = self._lex.current_number
        elif self._accept(Symbol.LParen):
            context.is_simple_constant = False
            self._parse_sum(context)
            self._expect(Symbol.RParen)
        elif self._accept(Symbol.Char):
            val = self._lex.current_string
            if val == "\\n":
                val = "\n"
            elif val == "\\r":
                val = "\r"
            if val == "\\t":
                val = "\t"
            if val == "\\0":
                val = "\0"

            if len(val) != 1:
                self._error("Expected exactly one character in single quotes!")
            if context.expect_16bit:
                context.append_code(f"PUSH16 #{ord(val)}")
            else:
                context.append_code(f"PUSH {ord(val)}")
            context.simple_value = ord(val)

        elif self._accept(Symbol.Call):
            self._parse_function_call(context, inside_expression=True)

        else:
            self._error("factor: syntax error")

    def _parse_logical(self, context: ExprContext):
        self._parse_sum(context)
        while self._lex.current in (Symbol.Equals, Symbol.NotEqual, Symbol.Ge, Symbol.Gt, Symbol.Le, Symbol.Lt):
            context.is_simple_constant = False
            v = self._lex.current
            self._lex.next_symbol()
            self._parse_sum(context)
            if v == Symbol.Equals:
                opcode = "EQ" if not context.expr_is16bit else "EQ16"
            elif v == Symbol.NotEqual:
                opcode = "NE" if not context.expr_is16bit else "NE16"
            elif v == Symbol.Gt:
                opcode = "LESS" if not context.expr_is16bit else "LESS16"  # inverse because of order on stack
            elif v == Symbol.Ge:
                opcode = "LESS_OR_EQ" if not context.expr_is16bit else "LESS_OR_EQ16"
            elif v == Symbol.Lt:
                opcode = "GREATER" if not context.expr_is16bit else "GREATER16"
            elif v == Symbol.Le:
                opcode = "GREATER_OR_EQ" if not context.expr_is16bit else "GREATER_OR_EQ16"
            else:
                raise NotImplementedError(self._lex.current)
            context.expr_is16bit = False  # bool result is 8-bit
            context.append_code(opcode)

    def _parse_logical_chain(self, context: ExprContext):
        self._parse_logical(context)
        has_chain = False
        while self._lex.current in (Symbol.And, Symbol.Or):
            context.is_simple_constant = False
            # TODO: precedence
            if self._accept(Symbol.Or):
                has_chain = True
                context.append_code("DUP\nJT" if not context.expect_16bit else "DUP16\nJT16", newline=False)
                context.append_code(f" @cond{self._condition_counter}_expr_end")
                self._parse_logical(context)
                context.append_code("OR")
                if context.expect_16bit:
                    context.append_code("EXTEND")
            elif self._accept(Symbol.And):
                has_chain = True
                context.append_code("DUP\nJF" if not context.expect_16bit else "DUP16\nJF16", newline=False)
                context.append_code(f" @cond{self._condition_counter}_expr_end")
                self._parse_logical(context)
                context.append_code("AND")
                if context.expect_16bit:
                    context.append_code("EXTEND")
        if has_chain:
            context.append_code(f":cond{self._condition_counter}_expr_end")
            self._condition_counter += 1

    def _parse_term(self, context: ExprContext):
        self._parse_factor(context)
        while self._lex.current in (Symbol.Mult, Symbol.Divide, Symbol.Modulo, Symbol.Ampersand, Symbol.Lsh, Symbol.Rsh):
            context.is_simple_constant = False
            context.expect_16bit = context.expr_is16bit
            v = self._lex.current
            self._lex.next_symbol()
            self._parse_factor(context)
            if v == Symbol.Mult:
                opcode = "MUL" if not context.expect_16bit else "MUL16"
            elif v == Symbol.Divide:
                opcode = "DIV2" if not context.expect_16bit else "SWAP16\nDIV16"  # div16 not implemented
            elif v == Symbol.Modulo:
                opcode = "SWAP\nMOD" if not context.expect_16bit else "SWAP16\nMOD16"
            elif v == Symbol.Ampersand:
                opcode = "AND" if not context.expect_16bit else "AND16"
            elif v == Symbol.Lsh:
                opcode = "LSH" if not context.expect_16bit else "LSH16"
            elif v == Symbol.Rsh:
                opcode = "RSH" if not context.expect_16bit else "RSH16"
            else:
                raise NotImplementedError(self._lex.current)
            context.append_code(opcode)

    def _parse_sum(self, context: ExprContext):
        unary_minus = False
        negate = False

        if self._lex.current == Symbol.Minus:
            unary_minus = True
            self._lex.next_symbol()
        elif self._lex.current == Symbol.Tilde:
            negate = True
            self._lex.next_symbol()

        self._parse_term(context)

        if unary_minus:
            context.append_code("NEG" if not (context.expect_16bit or context.expr_is16bit) else "NEG16")  # not yet implemented
        if negate:
            context.append_code("FLIP" if not (context.expect_16bit or context.expr_is16bit) else "FLIP16")

        while self._lex.current in (Symbol.Plus, Symbol.Minus, Symbol.Pipe, Symbol.Hat):
            context.is_simple_constant = False
            context.expect_16bit = context.expr_is16bit
            v = self._lex.current
            self._lex.next_symbol()
            self._parse_term(context)

            if v == Symbol.Plus:
                op = "ADD"
            elif v == Symbol.Minus:
                op = "SUB2"
            elif v == Symbol.Pipe:
                op = "OR"
            elif v == Symbol.Hat:
                op = "XOR"
            else:
                raise NotImplementedError(v)

            context.append_code(op if not context.expect_16bit else f"{op}16")

    def _parse_expression_typed(self, expect_16bit=False) -> ExprContext:
        lex_backup = self._lex.backup_state()
        cond_backup = self._condition_counter

        context = self._create_ec()
        context.dry_run = True
        context.expect_16bit = False
        self._parse_logical_chain(context)

        self._lex.restore_state(lex_backup)
        self._condition_counter = cond_backup

        downcast = context.expr_is16bit and not expect_16bit

        context = self._create_ec()
        context.expect_16bit = expect_16bit
        self._parse_logical_chain(context)

        if downcast:
            context.append_code("DOWNCAST")
        return context

    def _generate_struct_address(self, var: Variable, var_name: str, context: ExprContext) -> Variable:
        """ Generates instructions to compute address of last member in struct chain
         Returns this last member variable """
        current_struct = var.struct_def
        if not current_struct:
            self._error("Expected structure")
        struct_beginning = True
        while 1:
            if self._accept(Symbol.LBracket):
                self._parse_expression_typed(expect_16bit=True)  # index of element
                # if struct beginning, do full jump (array of struct), otherwise element jump
                element_size = var.stack_size if struct_beginning else var.stack_size_single_element
                context.append_code(f"PUSH16 #{element_size}")
                context.append_code("MUL16")
                if struct_beginning:
                    # dynamic array - add calculated address to pointer
                    struct_beginning = False
                    self._gen_load_store_instruction(var_name, True, context)  # load arr ptr
                    context.append_code("ADD16")
                # else: is a static array
                self._expect(Symbol.RBracket)
            else:
                if struct_beginning:
                    struct_beginning = False
                    if var.is_arg:
                        self._gen_load_store_instruction(var_name, True, context)  # load ptr
                    else:
                        self._gen_address_of_variable(var_name, context)

            if self._accept(Symbol.Dot):
                self._expect(Symbol.Identifier)
                struct_member = self._lex.current_identifier
                member_variable = current_struct.members[struct_member]

                var = member_variable
                if var.struct_def:
                    current_struct = var.struct_def
                else:
                    offset = current_struct.member_offset(struct_member)
                    context.append_code(f"PUSH16 #{offset}")
                    context.append_code("ADD16")
                    break
            else:
                break
        return var

    def _parse_statement(self, inside_loop=0, inside_if=False, inside_function=False):
        if self._lex.current in (Symbol.Byte, Symbol.Addr):
            var_type = Type.Byte if self._lex.current == Symbol.Byte else Type.Addr
            self._lex.next_symbol()
            self._expect(Symbol.Identifier)
            var_name = self._lex.current_identifier

            if self._accept(Symbol.LBracket):
                self._gen_array_initialization(self._create_ec(), var_name, var_type)
                self._expect(Symbol.Semicolon)
            else:
                self._register_variable(var_name, var_type)

                if self._accept(Symbol.Becomes):  # initial value, like byte A = 1;
                    self._parse_expression_typed(expect_16bit=var_type.size == 2)
                    self._gen_load_store_instruction(var_name, False, self._create_ec())
                self._expect(Symbol.Semicolon)

        elif self._lex.current == Symbol.Identifier and self._lex.current_identifier in self._struct_definitions:
            # struct init
            struct_name = self._lex.current_identifier
            struct_def = self._struct_definitions[struct_name]
            self._lex.next_symbol()
            self._expect(Symbol.Identifier)
            var_name = self._lex.current_identifier

            if self._accept(Symbol.LBracket):  # array of struct
                self._gen_array_initialization(self._create_ec(), var_name, struct_def=struct_def)
            elif self._accept(Symbol.Becomes):
                self._error("Cannot assign directly to structure")

            else:
                self._register_variable(var_name, Type.Struct, struct_def=struct_def)
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.Identifier):
            var_name = self._lex.current_identifier
            if self._accept(Symbol.LParen):
                # Non-returning intrinsics
                self._parse_intrinsic(var_name, self._create_ec(), expected_return=False)
                self._expect(Symbol.Semicolon)
                return

            var = self._get_variable(var_name)
            if var.struct_def:
                # LHS structure element assignment
                last_var_in_chain = self._generate_struct_address(var, var_name, self._create_ec())

                self._expect(Symbol.Becomes)
                self._parse_expression_typed(expect_16bit=last_var_in_chain.type.size == 2)

                if not last_var_in_chain.is_16bit:
                    self._append_code("STORE_GLOBAL2")
                else:
                    self._append_code("STORE_GLOBAL216")

                self._expect(Symbol.Semicolon)

            elif self._accept(Symbol.Becomes):
                # Simple LHS variable assignment
                self._parse_expression_typed(expect_16bit=var.is_16bit)
                self._gen_load_store_instruction(var_name, False, self._create_ec())
                self._expect(Symbol.Semicolon)
            elif self._accept(Symbol.LBracket):
                # Array element LHS assignment
                element_size = var.type.size
                if self._accept(Symbol.RBracket):
                    # arr[] = the same as arr[0], no skip to calculate
                    self._expect(Symbol.Becomes)
                    var_def = self._gen_load_store_instruction(var_name, True, self._create_ec())
                    if not var_def.is_array:
                        self._error(f"Variable {var} is not an array!")
                else:
                    var_def = self._gen_load_store_instruction(var_name, True, self._create_ec())
                    self._parse_expression_typed(expect_16bit=True)
                    if element_size > 1:
                        self._append_code(f"PUSH16 #{element_size}")
                        self._append_code("MUL16")

                    self._expect(Symbol.RBracket)
                    self._expect(Symbol.Becomes)
                    if not var_def.is_array:
                        self._error(f"Variable {var} is not an array!")
                    self._append_code("ADD16")
                    # do not use is_16bit there - we need type of element of array
                self._parse_expression_typed(expect_16bit=element_size == 2)
                # stack is in wrong order, fix it:
                if element_size == 1:
                    self._append_code("STORE_GLOBAL2")
                else:
                    self._append_code("STORE_GLOBAL216")

                self._expect(Symbol.Semicolon)
        elif self._accept(Symbol.Global):
            if not inside_function:
                self._error("Global is allowed only inside functions!")
            self._expect(Symbol.Identifier)
            if self._lex.current_identifier not in self._local_variables[""]:
                self._error(f"Unknown global variable {self._lex.current_identifier}")
            gvar = self._local_variables[""][self._lex.current_identifier]
            self._register_variable(self._lex.current_identifier, gvar.type, is_array=gvar.is_array, from_global=True, struct_def=gvar.struct_def)
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.Begin):
            cont = True
            while cont:
                self._parse_statement(inside_loop=inside_loop, inside_if=inside_if, inside_function=inside_function)
                if self._accept(Symbol.End):
                    break
            # self.expect(Symbol.End)
        elif self._accept(Symbol.If):
            # TODO: optimize unnecessary jumps if IF without ELSE
            no = self._if_counter
            self._if_counter += 1  # increment right away, because we may nest code
            ctx = self._create_ec()
            self._parse_logical_chain(ctx)

            self._append_code(f"JF @if{no}_else" if not ctx.expr_is16bit else f"JF16 @if{no}_else")

            inside_if = True

            self._expect(Symbol.Then)
            self._parse_statement(inside_loop=inside_loop, inside_if=inside_if, inside_function=inside_function)
            self._append_code(f"JMP @if{no}_endif")
            self._append_code(f":if{no}_else")

            if self._accept(Symbol.Else):
                if not inside_if:
                    self._error("Else outside IF")
                self._parse_statement(inside_loop=inside_loop, inside_if=inside_if, inside_function=inside_function)

            self._append_code(f":if{no}_endif")

        elif self._accept(Symbol.While):
            no = self._while_counter
            self._while_counter += 1
            self._append_code(f":while{no}_begin")
            ctx = self._create_ec()
            self._parse_logical_chain(ctx)
            self._append_code(f"JF @while{no}_endwhile" if not ctx.expr_is16bit else f"JF16 @while{no}_endwhile")

            self._expect(Symbol.Do)

            self._parse_statement(inside_loop=no, inside_if=inside_if, inside_function=inside_function)

            self._append_code(f"JMP @while{no}_begin")
            self._append_code(f":while{no}_endwhile")

        elif self._accept(Symbol.Do):
            no = self._while_counter
            self._while_counter += 1
            self._append_code(f":while{no}_begin")
            self._parse_statement(inside_loop=no, inside_if=inside_if, inside_function=inside_function)
            self._expect(Symbol.While)
            ctx = self._create_ec()
            self._parse_logical_chain(ctx)
            self._append_code(f"JT @while{no}_begin" if not ctx.expr_is16bit else f"JT16 @while{no}_begin")
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.Break):
            self._expect(Symbol.Semicolon)
            if not inside_loop:
                self._error("Break outside loop")
            self._append_code(f"JMP @while{inside_loop}_endwhile")

        elif self._accept(Symbol.Continue):
            self._expect(Symbol.Semicolon)
            if not inside_loop:
                self._error("Continue outside loop")
            self._append_code(f"JMP @while{inside_loop}_begin")

        elif self._accept(Symbol.Call):
            self._parse_function_call(self._create_ec())

        elif self._accept(Symbol.Return):
            if not inside_function:
                self._error("Return outside function")

            if not self._accept(Symbol.Semicolon):
                ctx = self._create_ec()
                self._parse_logical_chain(ctx)
                self._expect(Symbol.Semicolon)
                self._gen_load_store_instruction(FunctionSignature.RETURN_VALUE_NAME, False, ctx)

            self._append_code("RET")

        elif self._accept(Symbol.Print):
            if self._accept(Symbol.String):
                self._gen_address_of_str(self._lex.current_string, self._create_ec())
                self._append_code("SYSCALL Std.PrintString")
            else:
                ctx = self._create_ec()
                self._parse_logical_chain(ctx)
                if not ctx.expr_is16bit:
                    self._append_code("SYSCALL Std.PrintInt\nPOP")
                else:
                    self._append_code("SYSCALL Std.PrintInt16\nPOPN 2")
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.PrintChar):
            ctx = self._create_ec()
            self._parse_sum(ctx)
            if not ctx.expr_is16bit:
                self._append_code("SYSCALL Std.PrintCharPop")
            else:
                self._append_code("POP\nSYSCALL Std.PrintCharPop")
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.PrintStr):
            # print string from pointer
            self._parse_expression_typed(expect_16bit=True)
            self._append_code("SYSCALL Std.PrintString")
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.PrintNewLine):
            self._append_code("SYSCALL Std.PrintNewLine")
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.Debugger):
            self._append_code("debugger")
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.Halt):
            self._append_code("HALT")
            self._expect(Symbol.Semicolon)

        else:
            self._error("parse statement")

    def _parse_function_call(self, context: ExprContext, inside_expression=False):
        self._expect(Symbol.Identifier)
        func = self._lex.current_identifier
        if func not in self._function_signatures:
            self._error(f"Unknown function {func}")
        signature = self._function_signatures[func]

        self._expect(Symbol.LParen)

        context.append_code(";" + func + str(signature))

        refs_mapping = {}

        return_value = signature.return_value

        if inside_expression and return_value is None:
            self._error(f"Function {func} does not return anything to be used in expression")

        if return_value is not None:
            context.append_code("PUSHN 1 ; rv" if not return_value.is_16bit else "PUSHN 2 ; rv")

        first_arg = True
        for arg in signature.true_args:
            if not first_arg:
                self._expect(Symbol.Comma)
            first_arg = False
            if not arg.by_ref and not arg.struct_def:
                ctx2 = context.clone_with_same_buffer()
                ctx2.expect_16bit = arg.is_16bit
                self._parse_logical_chain(ctx2)
            elif arg.struct_def:
                # Structs are also passed by ref
                self._expect(Symbol.Identifier)
                var_name = self._lex.current_identifier
                self._generate_struct_address(self._get_variable(var_name), var_name, context)
                refs_mapping[arg] = self._lex.current_identifier

            else:
                self._expect(Symbol.Identifier)
                self._gen_load_store_instruction(self._lex.current_identifier, True, context)
                refs_mapping[arg] = self._lex.current_identifier

        self._expect(Symbol.RParen)

        if not inside_expression:
            self._expect(Symbol.Semicolon)
        context.append_code(f"CALL @function_{func}")

        context.append_code("; stack cleanup")
        for name, arg in reversed(signature.args.items()):
            if not arg.by_ref and not arg.struct_def:
                context.append_code(f"POPN {arg.stack_size} ; {name}")
            elif arg.struct_def:
                context.append_code(f"POPN 2 ; {name}")
            else:
                if arg != return_value:
                    self._gen_load_store_instruction(refs_mapping[arg], False, context)

        if return_value is not None and not inside_expression:
            # do not change POPN1 to POP, optimizer will take care
            context.append_code("POPN 1 ; rv" if not return_value.is_16bit else "POPN 2 ; rv")

    def _parse_block(self, inside_function=False):
        if self._accept(Symbol.EOF):
            return

        elif self._accept(Symbol.Const):
            if self._lex.current in (Symbol.Byte, Symbol.Addr):
                const_type = Type.Byte if self._lex.current == Symbol.Byte else Type.Addr
                self._lex.next_symbol()
                self._expect(Symbol.Identifier)
                const_name = self._lex.current_identifier
                self._expect(Symbol.Becomes)

                if self._accept(Symbol.Number):
                    const_value = self._lex.current_number
                elif self._accept(Symbol.Char):
                    const_value = ord(self._lex.current_string)
                else:
                    self._error("Const value must be number or char")
                    return

                self._expect(Symbol.Semicolon)
                self._register_constant(const_name, const_type, const_value)
            else:
                self._error("Constant must be a simple type")
        elif self._accept(Symbol.Function):
            self._expect(Symbol.Identifier)
            old_ctx = self._current_context
            self._current_context = self._lex.current_identifier

            signature = FunctionSignature()
            self._function_signatures[self._current_context] = signature

            self._expect(Symbol.LParen)

            while not self._accept(Symbol.RParen):
                if signature.args:
                    self._expect(Symbol.Comma)
                if self._lex.current in (Symbol.Byte, Symbol.Addr):
                    var_type = Type.Byte if self._lex.current == Symbol.Byte else Type.Addr
                    self._lex.next_symbol()
                    self._expect(Symbol.Identifier)
                    var_name = self._lex.current_identifier

                    if self._accept(Symbol.LBracket):
                        self._expect(Symbol.RBracket)
                        arg = Variable(var_type, is_array=True)
                    elif self._accept(Symbol.Ampersand):
                        arg = Variable(var_type, by_ref=True)
                    else:
                        arg = Variable(var_type)
                    arg.is_arg = True
                    signature.args[var_name] = arg
                elif self._lex.current_identifier in self._struct_definitions:
                    struct_def = self._struct_definitions[self._lex.current_identifier]
                    self._lex.next_symbol()
                    self._expect(Symbol.Identifier)
                    var_name = self._lex.current_identifier

                    if self._accept(Symbol.LBracket):
                        self._expect(Symbol.RBracket)
                        arg = Variable(Type.Struct, is_array=True, struct_def=struct_def)
                    else:
                        arg = Variable(Type.Struct, struct_def=struct_def)
                    arg.is_arg = True
                    signature.args[var_name] = arg
                else:
                    self._error("Expected type")

            if self._accept(Symbol.Arrow):
                if self._lex.current in (Symbol.Byte, Symbol.Addr):
                    ret_type = Type.Byte if self._lex.current == Symbol.Byte else Type.Addr
                    virtual_arg = Variable(ret_type, by_ref=True)
                    # Return value is like another function argument
                    virtual_arg.is_arg = True
                    signature.args[FunctionSignature.RETURN_VALUE_NAME] = virtual_arg
                    # Ensure the return value is first in args!
                    keys = [FunctionSignature.RETURN_VALUE_NAME]
                    for k in signature.args.keys():
                        if k != FunctionSignature.RETURN_VALUE_NAME:
                            keys.append(k)
                    signature.args = {k: signature.args[k] for k in keys}
                    self._lex.next_symbol()
                else:
                    self._error("Expected simple return type")

            if self._accept(Symbol.Semicolon):
                # just a declaration
                pass
            else:
                # definition
                self._parse_block(True)
                self._append_code("RET")
                self._generate_preamble()
                self._prepend_code(f":function_{self._current_context}\n;{signature}")
            self._current_context = old_ctx
        elif self._accept(Symbol.Struct):
            self._expect(Symbol.Identifier)
            struct_name = self._lex.current_identifier
            definition = StructDefinition(struct_name)
            self._struct_definitions[struct_name] = definition
            self._expect(Symbol.LParen)
            while not self._accept(Symbol.RParen):
                if definition.members:
                    self._expect(Symbol.Comma)
                if self._lex.current in (Symbol.Byte, Symbol.Addr):
                    var_type = Type.Byte if self._lex.current == Symbol.Byte else Type.Addr
                    self._lex.next_symbol()
                    self._expect(Symbol.Identifier)
                    var_name = self._lex.current_identifier

                    if self._accept(Symbol.LBracket):
                        self._expect(Symbol.Number)
                        size = self._lex.current_number
                        self._expect(Symbol.RBracket)
                        arg = Variable(var_type, is_array=True)
                        arg.array_fixed_size = size
                    else:
                        arg = Variable(var_type)
                    definition.members[var_name] = arg
                elif self._lex.current == Symbol.Identifier and self._lex.current_identifier in self._struct_definitions:
                    # nested struct
                    struct_name = self._lex.current_identifier
                    self._lex.next_symbol()
                    var_name = self._lex.current_identifier
                    self._lex.next_symbol()
                    if self._accept(Symbol.LBracket):
                        self._expect(Symbol.Number)
                        size = self._lex.current_number
                        self._expect(Symbol.RBracket)
                        arg = Variable(Type.Struct, is_array=True, struct_def=self._struct_definitions[struct_name])
                        arg.array_fixed_size = size
                    else:
                        arg = Variable(Type.Struct, struct_def=self._struct_definitions[struct_name])
                    definition.members[var_name] = arg

                else:
                    self._error("Expected type")
            self._expect(Symbol.Semicolon)
        else:
            self._parse_statement(inside_function=inside_function)

    def _generate_preamble(self):
        txt = ""
        if self._current_context not in self._local_variables:
            return
        total_stack_size = 0
        for k, var in self._local_variables[self._current_context].items():
            if not var.from_global:
                name = k
                if var.is_array:
                    name += "[]"
                if var.struct_def and not var.is_array:
                    total_stack_size += var.stack_size
                    txt += f"; struct {var.struct_def.name} {name}\n"
                else:
                    if var.is_array and var.array_fixed_size == 0:
                        # pointer
                        total_stack_size += 2
                    else:
                        # normal variable or array of known size from initializer list
                        total_stack_size += var.stack_size
                    txt += f"; {var.type.name} {name}\n"
        # todo: initial value instead of just push
        if total_stack_size > 0:
            txt += f"PUSHN {total_stack_size}\n"
            self._prepend_code(txt, False)

    def get_code(self) -> Sequence[str]:
        # "main" must be printed first to not execute functions
        if "" in self._codes:
            yield self._codes[""]
        for ctx, code in self._codes.items():
            if ctx:
                yield code
        for i, stc in enumerate(self._string_constants):
            yield f":string_{i + 1}"
            yield f"\"{stc}\""

    def print_code(self):
        print("\n".join(self.get_code()))

    def do_parse(self):
        self._lex.next_symbol()
        while not self._accept(Symbol.EOF):
            self._parse_block()
        self._current_context = ""
        self._append_code("HALT")
        self._generate_preamble()

    def optimize(self):
        for context, code in self._codes.items():
            c = optimize(code)
            self._codes[context] = c


if __name__ == '__main__':
    parser = Parser("""
// Test for found bug
addr jump_cache[10];
addr cache_pointer[] = jump_cache;
// here was 8bit instead of 16
addr X = succ(cache_pointer[]);

// Bug2: after EXTEND, not switching to 16bit
addr loc[];
byte L;
loc[] = L+1;
    """)
    parser.do_parse()
    parser.print_code()
