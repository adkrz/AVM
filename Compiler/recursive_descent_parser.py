from symbols import *

from lexer import Lexer, Symbol
from ast import AstProgram, VariableUsageLHS, VariableUsageRHS, BinaryOperation, Number, \
    Assign, Function, AbstractBlock, AbstractStatement, BinOpType, GroupOfStatements, \
    AbstractExpression, ConstantUsage, Condition, LogicalOperation, SumOperation, UnaryOperation, UnOpType, \
    MultiplyOperation, LogicalChainOperation, Instruction_PrintStringConstant, Instruction_PrintInteger, \
    Instruction_PrintNewLine, Instruction_PrintStringByPointer, Instruction_PrintChar, Instruction_Halt, \
    Instruction_Debugger, WhileLoop, DoWhileLoop, Instruction_Break, Instruction_Continue, FunctionCall, FunctionReturn, \
    ReturningCall, ArrayInitializationStatement, ArrayInitialization_InitializerList, ArrayInitialization_Pointer, \
    ArrayInitialization_StackAlloc, VariableUsage


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

    def _register_variable(self, name: str, type_: Type, is_array: bool = False, from_global: bool = False,
                           struct_def: Optional[StructDefinition] = None) -> Variable:
        if self._current_context in self._function_signatures:
            if name in self._function_signatures[self._current_context].args:
                return self._function_signatures[self._current_context].args[name]
        vdef = Variable(name, type_, is_array=is_array, from_global=from_global, struct_def=struct_def)
        if self._current_context not in self._local_variables:
            self._local_variables[self._current_context] = {name: vdef}
        else:
            if name not in self._local_variables[self._current_context]:
                self._local_variables[self._current_context][name] = vdef
        return vdef

    def _register_constant(self, name: str, type_: Type, value: int) -> Constant:
        cdef = Constant(name, type_, value)
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
        if self._current_context in self._function_signatures and name in self._function_signatures[
            self._current_context].args:
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
        raise Exception(f"Error in line {self._lex.line_number}: {what}")

    def _gen_array_initialization(self, context: ExprContext, new_var_name: str, new_var_type: Optional[Type] = None,
                                  struct_def=None) -> (Variable, ArrayInitializationStatement):
        vtype = Type.Struct if struct_def else new_var_type
        vdef = self._register_variable(new_var_name, vtype, is_array=True, struct_def=struct_def)

        node = None
        if self._accept(Symbol.RBracket):
            if self._accept(Symbol.Becomes):
                if self._accept(Symbol.LCurly):
                    node = ArrayInitialization_InitializerList(vdef)
                    size = 0
                    while 1:
                        if size > 0:
                            self._expect(Symbol.Comma)
                        self._expect(Symbol.Number)
                        size += 1
                        node.elements.append(self._lex.current_number)
                        if self._accept(Symbol.RCurly):
                            break
                        vdef.array_fixed_len = size
                else:
                    # this is a raw pointer, no memory reservation, but read address
                    expr = self._parse_expression()
                    node = ArrayInitialization_Pointer(vdef, expr)
            return vdef, node

        size_expr = self._parse_expression()

        self._expect(Symbol.RBracket)
        node = ArrayInitialization_StackAlloc(vdef, size_expr)
        return vdef, node

    def _gen_index_of_str(self, string_constant: str):
        if string_constant not in self._string_constants:
            self._string_constants.append(string_constant)
            index = len(self._string_constants)
        else:
            index = self._string_constants.index(self._lex.current_string) + 1
        return index

    def _gen_address_of_str(self, string_constant: str, context: ExprContext):
        index = self._gen_index_of_str(string_constant)
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
        # self._expect(Symbol.LParen)
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

    def _parse_factor(self, context: ExprContext) -> AbstractExpression:
        if self._accept(Symbol.Hash):
            context.expr_is16bit = True
            self._expect(Symbol.Number)
            return Number(self._lex.current_number, Type.Addr)
        elif self._accept(Symbol.Identifier):
            var = self._lex.current_identifier

            if self._accept(Symbol.LParen):
                # Intrinsics that return value
                return self._parse_intrinsic(var, context, expected_return=True)

            constant = self._get_constant(var)
            if constant is not None:
                return ConstantUsage(constant)

            var_def = self._get_variable(var)
            node = VariableUsageRHS(var_def)

            if var_def.struct_def:
                last_var_in_chain, node = self._generate_struct_address(var_def, var, context)
                return node

            if self._accept(Symbol.LBracket):
                if not var_def.is_array:
                    self._error(f"Variable {var} is not an array!")

                if self._accept(Symbol.RBracket):
                    # arr[] is the same as arr[0]
                    pass
                else:
                    expr = self._parse_expression()
                    self._expect(Symbol.RBracket)
                    node.array_jump = expr

            return node
        elif self._accept(Symbol.Number):
            number_type = Type.Byte if self._lex.current_number <= 255 else Type.Addr
            return Number(self._lex.current_number, number_type)
        elif self._accept(Symbol.LParen):
            context.is_simple_constant = False
            node = self._parse_sum(context)
            self._expect(Symbol.RParen)
            return node
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

            return Number(ord(val), Type.Byte)

        elif self._accept(Symbol.Call):
            fcall = self._parse_function_call(context, inside_expression=True)
            if not isinstance(fcall, ReturningCall):
                self._error("Expected function returning value")
            return fcall

        else:
            self._error("factor: syntax error")

    def _parse_logical(self, context: ExprContext) -> AbstractExpression:
        node = self._parse_sum(context)
        while self._lex.current in (Symbol.Equals, Symbol.NotEqual, Symbol.Ge, Symbol.Gt, Symbol.Le, Symbol.Lt):
            v = self._lex.current
            self._lex.next_symbol()
            expr = self._parse_sum(context)
            if v == Symbol.Equals:
                op = BinOpType.Equals
            elif v == Symbol.NotEqual:
                op = BinOpType.NotEqual
            elif v == Symbol.Gt:
                op = BinOpType.Gt
            elif v == Symbol.Ge:
                op = BinOpType.Ge
            elif v == Symbol.Lt:
                op = BinOpType.Lt
            elif v == Symbol.Le:
                op = BinOpType.Le
            else:
                raise NotImplementedError(self._lex.current)

            old_node = node
            node = LogicalOperation(op)
            node.operand1 = old_node
            node.operand2 = expr
        return node

    def _parse_expression(self) -> AbstractExpression:
        return self._parse_logical_chain(self._create_ec())

    def _parse_logical_chain(self, context: ExprContext) -> AbstractExpression:
        node = self._parse_logical(context)
        has_chain = False
        while self._lex.current in (Symbol.And, Symbol.Or):
            context.is_simple_constant = False
            if self._accept(Symbol.Or):
                has_chain = True

                expr = self._parse_logical(context)
                old_node = node
                node = LogicalChainOperation(BinOpType.LogicalOr)
                node.operand1 = old_node
                node.operand2 = expr

            elif self._accept(Symbol.And):
                has_chain = True

                expr = self._parse_logical(context)
                old_node = node
                node = LogicalChainOperation(BinOpType.LogicalAnd)
                node.operand1 = old_node
                node.operand2 = expr

        if has_chain:
            self._condition_counter += 1
        return node

    def _parse_term(self, context: ExprContext) -> AbstractExpression:
        node = self._parse_factor(context)
        while self._lex.current in (
                Symbol.Mult, Symbol.Divide, Symbol.Modulo, Symbol.Ampersand, Symbol.Lsh, Symbol.Rsh):
            context.is_simple_constant = False
            context.expect_16bit = context.expr_is16bit
            v = self._lex.current
            self._lex.next_symbol()
            node2 = self._parse_factor(context)

            old_node = node
            node = None

            if v == Symbol.Mult:
                op_ = BinOpType.Mul
                node = MultiplyOperation(op_)  # specialization important for constant folding
            elif v == Symbol.Divide:
                op_ = BinOpType.Div
            elif v == Symbol.Modulo:
                op_ = BinOpType.Mod
            elif v == Symbol.Ampersand:
                op_ = BinOpType.BitAnd
            elif v == Symbol.Lsh:
                op_ = BinOpType.Lsh
            elif v == Symbol.Rsh:
                op_ = BinOpType.Rsh
            else:
                raise NotImplementedError(self._lex.current)

            if node is None:
                node = BinaryOperation(op_)
            node.operand1 = old_node
            node.operand2 = node2

        return node

    def _parse_sum(self, context: ExprContext) -> AbstractExpression:
        unary_minus = False
        negate = False

        if self._lex.current == Symbol.Minus:
            unary_minus = True
            self._lex.next_symbol()
        elif self._lex.current == Symbol.Tilde:
            negate = True
            self._lex.next_symbol()

        node = self._parse_term(context)

        if unary_minus:
            node = UnaryOperation(UnOpType.UnaryMinus, node)
        if negate:
            node = UnaryOperation(UnOpType.BitNegate, node)

        while self._lex.current in (Symbol.Plus, Symbol.Minus, Symbol.Pipe, Symbol.Hat):
            context.is_simple_constant = False
            context.expect_16bit = context.expr_is16bit
            v = self._lex.current
            self._lex.next_symbol()
            node2 = self._parse_term(context)

            old_node = node
            node = None

            if v == Symbol.Plus:
                op_ = BinOpType.Add
                node = SumOperation(op_)
            elif v == Symbol.Minus:
                op_ = BinOpType.Sub
            elif v == Symbol.Pipe:
                op_ = BinOpType.BitOr
            elif v == Symbol.Hat:
                op_ = BinOpType.BitXor
            else:
                raise NotImplementedError(v)

            if node is None:
                node = BinaryOperation(op_)

            node.operand1 = old_node
            node.operand2 = node2
        return node

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

    def _generate_struct_address(self, var: Variable, var_name: str, context: ExprContext) -> (Variable, VariableUsage):
        """ Generates instructions to compute address of last member in struct chain
         Returns this last member variable """
        current_struct = var.struct_def
        if not current_struct:
            self._error("Expected structure")
        ret = VariableUsage(var)
        current_level = ret
        while 1:
            if self._accept(Symbol.LBracket):
                jmp = self._parse_expression()  # index of element
                current_level.array_jump = jmp
                self._expect(Symbol.RBracket)

            if self._accept(Symbol.Dot):
                self._expect(Symbol.Identifier)
                struct_member = self._lex.current_identifier
                member_variable = current_struct.members[struct_member]

                var = member_variable
                child_node = VariableUsage(var)
                current_level.struct_child = child_node
                if var.struct_def:
                    current_struct = var.struct_def
                else:
                    break
            else:
                break
        return var, ret

    def _parse_statement(self, inside_loop=0, inside_if=False, inside_function=False) -> Optional[AbstractStatement]:
        if self._lex.current in (Symbol.Byte, Symbol.Addr):
            var_type = Type.Byte if self._lex.current == Symbol.Byte else Type.Addr
            self._lex.next_symbol()
            self._expect(Symbol.Identifier)
            var_name = self._lex.current_identifier

            if self._accept(Symbol.LBracket):
                _, node = self._gen_array_initialization(self._create_ec(), var_name, var_type)
                self._expect(Symbol.Semicolon)
                return node
            else:
                var_def = self._register_variable(var_name, var_type)
                stmt = None
                if self._accept(Symbol.Becomes):  # initial value, like byte A = 1;
                    decl = VariableUsageLHS(var_def)
                    val = self._parse_logical_chain(self._create_ec())
                    stmt = Assign(decl, val)
                self._expect(Symbol.Semicolon)
                return stmt

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
                last_var_in_chain, struct_node = self._generate_struct_address(var, var_name, self._create_ec())

                self._expect(Symbol.Becomes)
                value = self._parse_expression()

                self._expect(Symbol.Semicolon)

                node = Assign(struct_node, value)
                return node

            elif self._accept(Symbol.Becomes):
                # Simple LHS variable assignment
                node2 = self._parse_expression()
                self._expect(Symbol.Semicolon)

                node = Assign(VariableUsageLHS(self._get_variable(var_name)), node2)
                return node
            elif self._accept(Symbol.LBracket):
                # Array element LHS assignment
                node = VariableUsageLHS(self._get_variable(var_name))
                element_size = var.type.size
                if self._accept(Symbol.RBracket):
                    # arr[] = the same as arr[0], no skip to calculate
                    pass
                else:
                    var_def = self._gen_load_store_instruction(var_name, True, self._create_ec())
                    if not var_def.is_array:
                        self._error(f"Variable {var_name} is not an array")
                    jmp = self._parse_expression()
                    node.array_jump = jmp
                    self._expect(Symbol.RBracket)
                    self._expect(Symbol.Becomes)
                node2 = self._parse_expression()
                node = Assign(node, node2)
                self._expect(Symbol.Semicolon)
                return node
        elif self._accept(Symbol.Global):
            if not inside_function:
                self._error("Global is allowed only inside functions!")
            self._expect(Symbol.Identifier)
            if self._lex.current_identifier not in self._local_variables[""]:
                self._error(f"Unknown global variable {self._lex.current_identifier}")
            gvar = self._local_variables[""][self._lex.current_identifier]
            self._register_variable(self._lex.current_identifier, gvar.type, is_array=gvar.is_array, from_global=True,
                                    struct_def=gvar.struct_def)
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.Begin):
            stmt = GroupOfStatements([])
            cont = True
            while cont:
                s = self._parse_statement(inside_loop=inside_loop, inside_if=inside_if, inside_function=inside_function)
                if s:
                    stmt.statements.append(s)
                if self._accept(Symbol.End):
                    break
            return stmt
        elif self._accept(Symbol.If):
            # TODO: optimize unnecessary jumps if IF without ELSE
            no = self._if_counter
            cond = Condition(no)
            self._if_counter += 1  # increment right away, because we may nest code
            expr = self._parse_expression()
            cond.condition = expr

            inside_if = True

            self._expect(Symbol.Then)
            stmt = self._parse_statement(inside_loop=inside_loop, inside_if=inside_if, inside_function=inside_function)
            cond.if_body = stmt

            if self._accept(Symbol.Else):
                stmt = self._parse_statement(inside_loop=inside_loop, inside_if=inside_if,
                                             inside_function=inside_function)
                cond.else_body = stmt

            return cond

        elif self._accept(Symbol.While):
            no = self._while_counter
            self._while_counter += 1

            node = WhileLoop(no)

            expr = self._parse_expression()
            node.condition = expr

            self._expect(Symbol.Do)

            stmt = self._parse_statement(inside_loop=no, inside_if=inside_if, inside_function=inside_function)
            node.body = stmt

            return node

        elif self._accept(Symbol.Do):
            no = self._while_counter
            self._while_counter += 1
            node = DoWhileLoop(no)

            stmt = self._parse_statement(inside_loop=no, inside_if=inside_if, inside_function=inside_function)
            node.body = stmt
            self._expect(Symbol.While)
            expr = self._parse_expression()
            node.condition = expr
            self._expect(Symbol.Semicolon)
            return node

        elif self._accept(Symbol.Break):
            self._expect(Symbol.Semicolon)
            if not inside_loop:
                self._error("Break outside loop")
            return Instruction_Break()

        elif self._accept(Symbol.Continue):
            self._expect(Symbol.Semicolon)
            if not inside_loop:
                self._error("Continue outside loop")
            return Instruction_Continue()

        elif self._accept(Symbol.Call):
            return self._parse_function_call(self._create_ec())

        elif self._accept(Symbol.Return):
            if not inside_function:
                self._error("Return outside function")

            if not self._accept(Symbol.Semicolon):
                expr = self._parse_expression()
                self._expect(Symbol.Semicolon)
                return FunctionReturn(expr)
            else:
                return FunctionReturn(None)

        elif self._accept(Symbol.Print):
            if self._accept(Symbol.String):
                idx = self._gen_index_of_str(self._lex.current_string)
                instr = Instruction_PrintStringConstant(idx, self._lex.current_string)
            else:
                expr = self._parse_expression()
                instr = Instruction_PrintInteger(expr)
            self._expect(Symbol.Semicolon)
            return instr

        elif self._accept(Symbol.PrintChar):
            ctx = self._create_ec()
            expr = self._parse_sum(ctx)
            self._expect(Symbol.Semicolon)
            return Instruction_PrintChar(expr)

        elif self._accept(Symbol.PrintStr):
            # print string from pointer
            expr = self._parse_expression()
            self._expect(Symbol.Semicolon)
            return Instruction_PrintStringByPointer(expr)

        elif self._accept(Symbol.PrintNewLine):
            self._expect(Symbol.Semicolon)
            return Instruction_PrintNewLine()

        elif self._accept(Symbol.Debugger):
            self._expect(Symbol.Semicolon)
            return Instruction_Debugger()

        elif self._accept(Symbol.Halt):
            self._expect(Symbol.Semicolon)
            return Instruction_Halt()

        else:
            self._error("parse statement")

    def _parse_function_call(self, context: ExprContext, inside_expression=False) -> FunctionCall:
        self._expect(Symbol.Identifier)
        func = self._lex.current_identifier
        if func not in self._function_signatures:
            self._error(f"Unknown function {func}")
        signature = self._function_signatures[func]

        self._expect(Symbol.LParen)

        context.append_code(";" + func + str(signature))

        refs_mapping = {}

        return_value = signature.return_value

        node = FunctionCall(func, signature) if return_value is None else ReturningCall(func, signature)

        if inside_expression and return_value is None:
            self._error(f"Function {func} does not return anything to be used in expression")

        first_arg = True
        for arg in signature.true_args:
            if not first_arg:
                self._expect(Symbol.Comma)
            first_arg = False
            if not arg.by_ref and not arg.struct_def:
                expr = self._parse_expression()
                node.arguments.append(expr)

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

        return node

    def _parse_block(self, inside_function=False) -> Optional[AbstractBlock]:
        if self._accept(Symbol.EOF):
            return None

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
                    const_value = 0
                    self._error("Const value must be number or char")

                cdef = self._register_constant(const_name, const_type, const_value)
                self._expect(Symbol.Semicolon)

                return None
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
                        arg = Variable(var_name, var_type, is_array=True)
                    elif self._accept(Symbol.Ampersand):
                        arg = Variable(var_name, var_type, by_ref=True)
                    else:
                        arg = Variable(var_name, var_type)
                    arg.is_arg = True
                    signature.args[var_name] = arg
                elif self._lex.current_identifier in self._struct_definitions:
                    struct_def = self._struct_definitions[self._lex.current_identifier]
                    self._lex.next_symbol()
                    self._expect(Symbol.Identifier)
                    var_name = self._lex.current_identifier

                    if self._accept(Symbol.LBracket):
                        self._expect(Symbol.RBracket)
                        arg = Variable(var_name, Type.Struct, is_array=True, struct_def=struct_def)
                    else:
                        arg = Variable(var_name, Type.Struct, struct_def=struct_def)
                    arg.is_arg = True
                    signature.args[var_name] = arg
                else:
                    self._error("Expected type")

            if self._accept(Symbol.Arrow):
                if self._lex.current in (Symbol.Byte, Symbol.Addr):
                    ret_type = Type.Byte if self._lex.current == Symbol.Byte else Type.Addr
                    virtual_arg = Variable(FunctionSignature.RETURN_VALUE_NAME, ret_type, by_ref=True)
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
                self._current_context = old_ctx
            else:
                # definition
                body = self._parse_block(True)
                node = Function(self._current_context, signature, body)
                self._current_context = old_ctx
                return node
            return None
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
                        arg = Variable(var_name, var_type, is_array=True)
                        arg.array_fixed_size = size
                    else:
                        arg = Variable(var_name, var_type)
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
                        arg = Variable(var_name, Type.Struct, is_array=True,
                                       struct_def=self._struct_definitions[struct_name])
                        arg.array_fixed_size = size
                    else:
                        arg = Variable(var_name, Type.Struct, struct_def=self._struct_definitions[struct_name])
                    definition.members[var_name] = arg

                else:
                    self._error("Expected type")
            self._expect(Symbol.Semicolon)
        else:
            stmt = self._parse_statement(inside_function=inside_function)
            return stmt

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

    def do_parse(self) -> AstProgram:
        node = AstProgram()
        self._lex.next_symbol()
        while not self._accept(Symbol.EOF):
            block = self._parse_block()
            if block:
                node.blocks.append(block)
        self._current_context = ""
        return node


if __name__ == '__main__':
    parser = Parser("""
addr a = 2+2*2;
    """)
    tree = parser.do_parse()
    #tree.print(0)
    opt = True
    while opt:
        opt = tree.optimize(None)
    code = tree.gen_code(None)
    code.print()
    pass
