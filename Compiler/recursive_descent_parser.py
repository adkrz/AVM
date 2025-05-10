from enum import Enum
from typing import Dict, Sequence, Optional

from lexer import Lexer, Symbol

"""
TODO:
structure expression that does not end on simple variable and can be passed to function under other type
pass struct to function
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
        self.array_fixed_size = 0
        self.is_arg = False

    @property
    def is_16bit(self):
        return self.is_array or (self.type != Type.Struct and self.type.size == 2)

    @property
    def stack_size(self):
        s = self.stack_size_single_element
        if self.array_fixed_size > 1:
            s *= self.array_fixed_size
        return s

    @property
    def stack_size_single_element(self):
        if self.type == Type.Struct:
            s = self.struct_def.stack_size
        else:
            s = 2 if self.is_16bit else 1
        return s


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


class Parser:
    def __init__(self, input_string: str):
        self._lex = Lexer(input_string)

        self._if_counter = 1
        self._while_counter = 1
        self._condition_counter = 1
        self._codes = {}  # per context
        self._local_variables: Dict[
            str, Dict[str, "Variable"]] = {}  # per context, then name+details, in order of occurrence
        self._current_context = ""  # empty = global, otherwise in function
        self._string_constants = []
        self._expr_is_16bit = False

        self._function_signatures: Dict[str, FunctionSignature] = {}
        self._struct_definitions: Dict[str, "StructDefinition"] = {}

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

    def _register_variable(self, name: str, type_: Type, is_array: bool = False, from_global: bool = False, struct_def: Optional[StructDefinition]=None) -> Variable:
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

    def _gen_load_store_instruction(self, name: str, load: bool, dry_run=False) -> "Variable":

        def gen(offset, is_arg, is_16bit):
            instr = "LOAD" if load else "STORE"
            bbits = "16" if is_16bit else ""
            origin = "ARG" if is_arg else "LOCAL"
            code = f"{instr}_{origin}{bbits} {offset} ; {name}"
            return code

        var = self._get_variable(name)
        offs = self._offsetof(name)

        if var.is_arg:
            if not dry_run:
                self._append_code(gen(offs, True, var.is_16bit))
        elif var.from_global:
            if not dry_run:
                bits = "16" if var.is_16bit else ""
                self._append_code("PUSH_STACK_START")
                if offs != 0:
                    self._append_code(f"PUSH16 #{offs}")
                    self._append_code("ADD16")
                if load:
                    self._append_code(f"LOAD_GLOBAL{bits}")
                else:
                    self._append_code(f"STORE_GLOBAL{bits}")
        else:
            if not dry_run:
                self._append_code(gen(offs, False, var.is_16bit))

        return var

    def _get_variable(self, name: str) -> Variable:
        # Check function arguments
        if (self._current_context in self._function_signatures and name
                in self._function_signatures[self._current_context].args):
            return self._function_signatures[self._current_context].args[name]

        if self._current_context not in self._local_variables:
            self._error(f"Current context is empty: {self._current_context}")

        # Check local variables, this includes global declarations
        if name not in self._local_variables[self._current_context]:
            self._error(f"Unknown variable {name}")
        return self._local_variables[self._current_context][name]

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
                    v = self._local_variables[""][name]
                    return offs
                offs += v.stack_size

        # Check local variables
        if name not in self._local_variables[self._current_context]:
            self._error(f"Unknown variable {name}")
        for k, v in self._local_variables[self._current_context].items():
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

    def _gen_array_initialization(self, new_var_name: str, new_var_type: Optional[Type] = None, struct_def=None) -> Variable:
        vtype = Type.Struct if struct_def else new_var_type
        vdef = self._register_variable(new_var_name, vtype, is_array=True, struct_def=struct_def)

        if self._accept(Symbol.RBracket):
            # this is a raw pointer, no memory reservation, but read address
            if self._accept(Symbol.Becomes):
                self._parse_expression_typed(expect_16bit=True)
                self._gen_load_store_instruction(new_var_name, False)
            return vdef

        self._append_code("PUSH_NEXT_SP")
        # PUSH_NEXT_SP actually pushes SP+addressSize, so move back:
        self._append_code("PUSH16 #2")
        self._append_code("SUB216")
        self._gen_load_store_instruction(new_var_name, False)
        self._parse_expression_typed(expect_16bit=False)  # size of array
        element_size = new_var_type.size if new_var_type else struct_def.stack_size
        if element_size > 1:
            # TODO: array size limitation - no 16 bit version of PUSHN2
            self._append_code(f"PUSH {element_size}")
            self._append_code(f"MUL")
        self._expect(Symbol.RBracket)
        self._append_code(f"PUSHN2 ; {new_var_name} alloc")
        return vdef

    def _gen_address_of_str(self, string_constant: str, dry_run=False):
        if string_constant not in self._string_constants:
            self._string_constants.append(string_constant)
            index = len(self._string_constants)
        else:
            index = self._string_constants.index(self._lex.current_string) + 1
        if not dry_run:
            self._append_code(f"PUSH16 @string_{index}")

    def _gen_address_of_variable(self, var_name, dry_run=False):
        var_def = self._get_variable(var_name)
        if not dry_run:
            if var_def.is_array:
                self._gen_load_store_instruction(var_name, True)
            elif var_def.from_global:
                self._append_code("PUSH_STACK_START")
                offset = self._offsetof(var_name)
                if offset > 0:
                    self._append_code(f"PUSH16 #{offset}")
                    self._append_code("ADD16")
            elif var_def.is_arg:
                self._append_code("PUSH_REG 2")
                self._append_code(f"PUSH16 #{self._offsetof(var_name)}")
                self._append_code("SUB16")
                self._append_code("PUSH16 #2")  # saved registers
                self._append_code("SUB16")
            else:
                self._append_code("PUSH_REG 2")
                self._append_code(f"PUSH16 #{self._offsetof(var_name)}")
                self._append_code("ADD16")

    def _parse_intrinsic(self, function_name, dry_run=False):
        self._expect(Symbol.LParen)
        if function_name == "sizeof":
            if self._accept(Symbol.Byte):
                if not dry_run:
                    self._append_code(f"PUSH {Type.Byte.size}")
            elif self._accept(Symbol.Addr):
                if not dry_run:
                    self._append_code(f"PUSH {Type.Addr.size}")
            else:
                self._expect(Symbol.Identifier)
                if self._lex.current_identifier in self._struct_definitions:
                    if not dry_run:
                        self._append_code(f"PUSH {self._struct_definitions[self._lex.current_identifier].stack_size}")
                else:
                    self._error(f"Unknown data type {self._lex.current_identifier}")
        elif function_name == "addressof":
            self._expr_is_16bit = True
            if self._accept(Symbol.String):
                self._gen_address_of_str(self._lex.current_string, dry_run)
            else:
                self._expect(Symbol.Identifier)
                self._gen_address_of_variable(self._lex.current_identifier, dry_run)
        else:
            self._error(f"Unknown function {function_name}")
        self._expect(Symbol.RParen)

    def _parse_factor(self, dry_run=False, expect_16bit=False):
        if self._accept(Symbol.Identifier):
            var = self._lex.current_identifier

            if var in ("sizeof", "addressof", "strlen"):
                self._parse_intrinsic(var, dry_run)
                return

            var_def = self._get_variable(var)

            if var_def.struct_def:
                last_var_in_chain = self._generate_struct_address(var_def, var)
                self._append_code("LOAD_GLOBAL") if not last_var_in_chain.is_16bit else self._append_code("LOAD_GLOBAL16")
                self._expr_is_16bit = last_var_in_chain.is_16bit
                return

            if self._accept(Symbol.LBracket):
                var_def = self._gen_load_store_instruction(var, True, dry_run=dry_run)
                if not var_def.is_array:
                    self._error(f"Variable {var} is not an array!")
                self._parse_expression_typed(expect_16bit=True)  # array indexes are 16bit
                self._expect(Symbol.RBracket)
                element_size = var_def.type.size
                if element_size > 1:
                    self._expr_is_16bit = True
                    if not dry_run:
                        self._append_code(f"PUSH16 #{element_size}")
                        self._append_code("MUL16")
                if not dry_run:
                    self._append_code("ADD16")
                    self._append_code("LOAD_GLOBAL") if element_size == 1 else self._append_code("LOAD_GLOBAL16")
            else:
                var_def = self._gen_load_store_instruction(var, True, dry_run=dry_run)
                if var_def.is_16bit:
                    self._expr_is_16bit = True
                if expect_16bit and not var_def.is_16bit:
                    if not dry_run:
                        self._append_code("EXTEND")
        elif self._accept(Symbol.Number):
            if self._lex.current_number > 255 or expect_16bit:
                self._expr_is_16bit = True
                if not dry_run:
                    self._append_code(f"PUSH16 #{self._lex.current_number}")
            else:
                if not dry_run:
                    self._append_code(f"PUSH {self._lex.current_number}")
        elif self._accept(Symbol.LParen):
            self._parse_expression(dry_run=dry_run, expect_16bit=expect_16bit)
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
            if not dry_run:
                if expect_16bit:
                    self._append_code(f"PUSH16 #{ord(val)}")
                else:
                    self._append_code(f"PUSH {ord(val)}")
        else:
            self._error("factor: syntax error")

    def _parse_logical(self, dry_run=False, expect_16bit=False):
        self._parse_factor(dry_run=dry_run, expect_16bit=expect_16bit)
        while self._lex.current in (Symbol.Equals, Symbol.NotEqual, Symbol.Ge, Symbol.Gt, Symbol.Le, Symbol.Lt):
            v = self._lex.current
            self._lex.next_symbol()
            self._parse_factor(dry_run=dry_run, expect_16bit=expect_16bit)
            if v == Symbol.Equals:
                opcode = "EQ" if not expect_16bit else "EQ16"
            elif v == Symbol.NotEqual:
                opcode = "NE" if not expect_16bit else "NE16"
            elif v == Symbol.Gt:
                opcode = "LESS_OR_EQ" if not expect_16bit else "LESS_OR_EQ16"
            elif v == Symbol.Ge:
                opcode = "LESS" if not expect_16bit else "LESS16"
            elif v == Symbol.Lt:
                opcode = "SWAP\nLESS" if not expect_16bit else "SWAP16\nLESS16"
            elif v == Symbol.Le:
                opcode = "SWAP\nLESS_OR_EQ" if not expect_16bit else "SWAP16\nLESS_OR_EQ16"
            else:
                raise NotImplementedError(self._lex.current)
            if not dry_run:
                self._append_code(opcode)

    def _parse_logical_chain(self, dry_run=False, expect_16bit=False):
        self._parse_logical(dry_run=dry_run, expect_16bit=expect_16bit)
        has_chain = False
        while self._lex.current in (Symbol.And, Symbol.Or):
            # TODO: precedence
            if self._accept(Symbol.Or):
                has_chain = True
                if not dry_run:
                    self._append_code("DUP\nJT" if not expect_16bit else "DUP16\nJT16", newline=False)
                    self._append_code(f" @cond{self._condition_counter}_expr_end")
                self._parse_logical(dry_run=dry_run, expect_16bit=expect_16bit)
                if not dry_run:
                    self._append_code("OR")
            elif self._accept(Symbol.And):
                has_chain = True
                if not dry_run:
                    self._append_code("DUP\nJF" if not expect_16bit else "DUP16\nJF16", newline=False)
                    self._append_code(f" @cond{self._condition_counter}_expr_end")
                self._parse_logical(dry_run=dry_run, expect_16bit=expect_16bit)
                if not dry_run:
                    self._append_code("AND")
        if has_chain:
            if not dry_run:
                self._append_code(f":cond{self._condition_counter}_expr_end")
                self._condition_counter += 1

    def _parse_term(self, dry_run=False, expect_16bit=False):
        self._parse_logical_chain(dry_run=dry_run, expect_16bit=expect_16bit)
        while self._lex.current in (Symbol.Mult, Symbol.Divide, Symbol.Modulo):
            v = self._lex.current
            self._lex.next_symbol()
            self._parse_logical_chain(dry_run=dry_run, expect_16bit=expect_16bit)
            if v == Symbol.Mult:
                opcode = "MUL" if not expect_16bit else "MUL16"
            elif v == Symbol.Divide:
                opcode = "SWAP\nDIV" if not expect_16bit else "SWAP16\nDIV16"
            elif v == Symbol.Modulo:
                opcode = "SWAP\nMOD" if not expect_16bit else "SWAP16\nMOD16"
            else:
                raise NotImplementedError(self._lex.current)
            if not dry_run:
                self._append_code(opcode)

    def _parse_expression(self, dry_run=False, expect_16bit=False):
        um = False
        if self._lex.current == Symbol.Plus or self._lex.current == Symbol.Minus:
            um = True
            self._lex.next_symbol()
        self._parse_term(dry_run=dry_run, expect_16bit=expect_16bit)
        if um and not dry_run:
            self._append_code("NEG" if not expect_16bit else "NEG16")  # not yet implemented
        while self._lex.current == Symbol.Plus or self._lex.current == Symbol.Minus:
            v = self._lex.current
            self._lex.next_symbol()
            self._parse_term(dry_run=dry_run, expect_16bit=expect_16bit)
            if not dry_run:
                if not expect_16bit:
                    self._append_code("ADD" if v == Symbol.Plus else "SUB2")
                else:
                    self._append_code("ADD16" if v == Symbol.Plus else "SUB216")

    def _parse_expression_typed(self, expect_16bit=False):
        self._expr_is_16bit = False
        lex_backup = self._lex.backup_state()
        cond_backup = self._condition_counter

        self._parse_expression(dry_run=True, expect_16bit=False)

        self._lex.restore_state(lex_backup)
        self._condition_counter = cond_backup

        downcast = self._expr_is_16bit and not expect_16bit

        self._parse_expression(dry_run=False, expect_16bit=expect_16bit)

        if downcast:
            self._append_code("SWAP\nPOP")

    def _generate_struct_address(self, var: Variable, var_name: str) -> Variable:
        """ Generates instructions to compute address of last member in struct chain
         Returns this last member variable """
        current_struct = var.struct_def
        if not current_struct:
            self._error("Expected structure")
        struct_beginning = True
        while 1:
            if var.is_array:
                self._expect(Symbol.LBracket)
                self._parse_expression_typed(expect_16bit=True)  # index of element
                # if struct beginning, do full jump (array of struct), otherwise element jump
                element_size = var.stack_size if struct_beginning else var.stack_size_single_element
                self._append_code(f"PUSH16 #{element_size}")
                self._append_code("MUL16")
                if struct_beginning:
                    # dynamic array - add calculated address to pointer
                    struct_beginning = False
                    self._gen_load_store_instruction(var_name, True)  # load arr ptr
                    self._append_code("ADD16")
                # else: is a static array
                self._expect(Symbol.RBracket)
            else:
                if struct_beginning:
                    struct_beginning = False
                    if var.is_arg:
                        self._gen_load_store_instruction(var_name, True)  # load ptr
                    else:
                        self._gen_address_of_variable(var_name)

            if self._accept(Symbol.Dot):
                self._expect(Symbol.Identifier)
                struct_member = self._lex.current_identifier
                member_variable = current_struct.members[struct_member]

                var = member_variable
                if var.struct_def:
                    current_struct = var.struct_def
                else:
                    offset = current_struct.member_offset(struct_member)
                    self._append_code(f"PUSH16 #{offset}")
                    self._append_code("ADD16")
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
                self._gen_array_initialization(var_name, var_type)
                self._expect(Symbol.Semicolon)
            else:
                self._register_variable(var_name, var_type)

                if self._accept(Symbol.Becomes):  # initial value, like byte A = 1;
                    self._parse_expression_typed(expect_16bit=var_type.size == 2)
                    self._gen_load_store_instruction(var_name, False)
                self._expect(Symbol.Semicolon)

        elif self._lex.current == Symbol.Identifier and self._lex.current_identifier in self._struct_definitions:
            # struct init
            struct_name = self._lex.current_identifier
            struct_def = self._struct_definitions[struct_name]
            self._lex.next_symbol()
            self._expect(Symbol.Identifier)
            var_name = self._lex.current_identifier

            if self._accept(Symbol.LBracket):  # array of struct
                self._gen_array_initialization(var_name, struct_def=struct_def)
            elif self._accept(Symbol.Becomes):
                self._error("Cannot assign directly to structure")

            else:
                self._register_variable(var_name, Type.Struct, struct_def=struct_def)
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.Identifier):
            var_name = self._lex.current_identifier
            var = self._get_variable(var_name)
            if var.struct_def:
                # LHS structure element assignment
                last_var_in_chain = self._generate_struct_address(var, var_name)

                self._expect(Symbol.Becomes)
                self._parse_expression_typed(expect_16bit=last_var_in_chain.type.size == 2)

                if not last_var_in_chain.is_16bit:
                    self._append_code("ROLL3")
                    self._append_code("STORE_GLOBAL")
                else:
                    self._append_code("SWAP16")
                    self._append_code("STORE_GLOBAL16")

                self._expect(Symbol.Semicolon)

            elif self._accept(Symbol.Becomes):
                # Simple LHS variable assignment
                self._parse_expression_typed(expect_16bit=var.type.size == 2)
                self._gen_load_store_instruction(var_name, False)
                self._expect(Symbol.Semicolon)
            elif self._accept(Symbol.LBracket):
                # Array element LHS assignment
                self._parse_expression_typed(expect_16bit=True)
                element_size = var.type.size
                if element_size > 1:
                    self._append_code(f"PUSH16 #{element_size}")
                    self._append_code("MUL16")
                self._expect(Symbol.RBracket)
                self._expect(Symbol.Becomes)
                var_def = self._gen_load_store_instruction(var_name, True)
                if not var_def.is_array:
                    self._error(f"Variable {var} is not an array!")
                self._append_code("ADD16")
                # do not use is_16bit there - we need type of element of array
                self._parse_expression_typed(expect_16bit=element_size == 2)
                # stack is in wrong order, fix it:
                if element_size == 1:
                    self._append_code("ROLL3")
                    self._append_code("STORE_GLOBAL")
                else:
                    self._append_code("SWAP16")
                    self._append_code("STORE_GLOBAL16")

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
            self._parse_expression_typed(expect_16bit=False)

            self._append_code(f"JF @if{no}_else")

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
            self._parse_expression_typed(expect_16bit=False)
            self._append_code(f"JF @while{no}_endwhile")

            self._expect(Symbol.Do)

            self._parse_statement(inside_loop=no, inside_if=inside_if, inside_function=inside_function)

            self._append_code(f"JMP @while{no}_begin")
            self._append_code(f":while{no}_endwhile")

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
            self._expect(Symbol.Identifier)
            func = self._lex.current_identifier
            if func not in self._function_signatures:
                self._error(f"Unknown function {func}")
            signature = self._function_signatures[func]

            self._expect(Symbol.LParen)

            self._append_code(";" + func + str(signature))

            refs_mapping = {}
            for i, arg in enumerate(signature.args.values()):
                if i > 0:
                    self._expect(Symbol.Comma)
                if not arg.by_ref and not arg.struct_def:
                    self._parse_expression_typed(expect_16bit=arg.is_16bit)
                else:
                    self._expect(Symbol.Identifier)
                    self._gen_load_store_instruction(self._lex.current_identifier, True)
                    refs_mapping[arg] = self._lex.current_identifier

            self._expect(Symbol.RParen)

            self._expect(Symbol.Semicolon)
            self._append_code(f"CALL @function_{func}")

            self._append_code("; stack cleanup")
            for arg in reversed(signature.args.values()):
                if not arg.by_ref and not arg.struct_def:
                    self._append_code(f"POPN {arg.type.size}")
                else:
                    self._gen_load_store_instruction(refs_mapping[arg], False)

        elif self._accept(Symbol.Return):
            if not inside_function:
                self._error("Return outside function")
            self._append_code("RET")
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.Print):
            if self._accept(Symbol.String):
                self._gen_address_of_str(self._lex.current_string)
                self._append_code("SYSCALL Std.PrintString")
            else:
                self._expr_is_16bit = False
                self._parse_expression()
                if not self._expr_is_16bit:
                    self._append_code("SYSCALL Std.PrintInt\nPOP")
                else:
                    self._append_code("SYSCALL Std.PrintInt16\nPOPN 2")
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.PrintChar):
            self._parse_expression()
            if not self._expr_is_16bit:
                self._append_code("SYSCALL Std.PrintCharPop")
            else:
                self._append_code("SWAP\nPOP\nSYSCALL Std.PrintCharPop")
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.PrintNewLine):
            self._append_code("SYSCALL Std.PrintNewLine")
            self._expect(Symbol.Semicolon)

        else:
            self._error("parse statement")

    def _parse_block(self, inside_function=False):
        if self._accept(Symbol.EOF):
            return

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
                    elif self._accept(Symbol.Reference):
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
                        arg = Variable(Type.Struct, struct_def=definition)
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
                    total_stack_size += var.stack_size if not var.is_array else 2
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


if __name__ == '__main__':
    parser = Parser("""
    byte x = 1;
    byte y = 1;
addr A[] = addressof(x);
A = addressof(y);
A[2] = 0;
    """)
    parser.do_parse()
    parser.print_code()
