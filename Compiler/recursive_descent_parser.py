from symbols import *

from lexer import Lexer, Symbol
from myast import AstProgram, VariableUsageLHS, VariableUsageRHS, BinaryOperation, Number, \
    Assign, Function, AbstractBlock, AbstractStatement, BinOpType, GroupOfStatements, \
    AbstractExpression, ConstantUsage, Condition, LogicalOperation, SumOperation, UnaryOperation, UnOpType, \
    MultiplyOperation, LogicalChainOperation, Instruction_PrintStringConstant, Instruction_PrintInteger, \
    Instruction_PrintNewLine, Instruction_PrintStringByPointer, Instruction_PrintChar, Instruction_Halt, \
    Instruction_Debugger, WhileLoop, DoWhileLoop, Instruction_Break, Instruction_Continue, FunctionCall, FunctionReturn, \
    ReturningCall, ArrayInitializationStatement, ArrayInitialization_InitializerList, ArrayInitialization_Pointer, \
    ArrayInitialization_StackAlloc, VariableUsage, SubtractOperation, Instruction_AddressOfString, \
    Instruction_AddressOfVariable, Syscall_ReadKey, Syscall_GetRandomNumber, NonReturningSyscall, \
    VariableUsageJustStructAddress
from symbol_table import SymbolTable


class Parser:
    def __init__(self, input_string: str):
        self._lex = Lexer(input_string)

        self._if_counter = 1
        self._while_counter = 1
        self._condition_counter = 1
        self._codes = {}  # per context
        self._current_context = ""  # empty = global, otherwise in function
        self.symbol_table = SymbolTable()

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

    def _gen_array_initialization(self, new_var_name: str, new_var_type: Optional[Type] = None,
                                  struct_def=None) -> (Variable, ArrayInitializationStatement):
        vtype = Type.Struct if struct_def else new_var_type
        vdef = self.symbol_table.register_variable(self._current_context, new_var_name, vtype, is_array=True,
                                                   struct_def=struct_def)

        node = None
        if self._accept(Symbol.RBracket):
            if self._accept(Symbol.Becomes):
                if self._accept(Symbol.LCurly):
                    node = ArrayInitialization_InitializerList(self._lex.line_number, vdef)
                    size = 0
                    while 1:
                        if size > 0:
                            self._expect(Symbol.Comma)
                        self._expect(Symbol.Number)
                        size += 1
                        node.elements.append(Number(self._lex.line_number,self._lex.current_number, new_var_type))
                        if self._accept(Symbol.RCurly):
                            break
                        vdef.array_fixed_len = size
                else:
                    # this is a raw pointer, no memory reservation, but read address
                    expr = self._parse_expression()
                    node = ArrayInitialization_Pointer(self._lex.line_number,vdef, expr)
            return vdef, node

        size_expr = self._parse_expression()

        self._expect(Symbol.RBracket)
        node = ArrayInitialization_StackAlloc(self._lex.line_number,vdef, size_expr)
        return vdef, node

    def _parse_intrinsic(self, function_name, expected_return) -> AbstractExpression:
        # self._expect(Symbol.LParen)
        ret = None
        if function_name == "sizeof":
            if self._accept(Symbol.Byte):
                ret = Number(self._lex.line_number, Type.Byte.size, Type.Byte)
            elif self._accept(Symbol.Addr):
                ret = Number(self._lex.line_number, Type.Addr.size, Type.Byte)
            else:
                self._expect(Symbol.Identifier)
                if struct_def := self.symbol_table.get_struct_definition(self._lex.current_identifier):
                    ret = Number(self._lex.line_number, struct_def.stack_size, Type.Byte)
                else:
                    self._error(f"Unknown data type {self._lex.current_identifier}")
        elif function_name == "length":
            self._expect(Symbol.Identifier)
            var = self.symbol_table.get_variable(self._current_context, self._lex.current_identifier)
            if not var.is_array:
                self._error(f"Variable {self._lex.current_identifier} is not an array")
            size = var.array_fixed_len if var.array_fixed_len > 0 else var.array_fixed_size
            if size <= 255:
                ret = Number(self._lex.line_number, size, Type.Byte)
            else:
                ret = Number(self._lex.line_number, size, Type.Addr)
        elif function_name == "addressof":
            if self._accept(Symbol.String):
                ret = Instruction_AddressOfString(self._lex.line_number, self._lex.current_string)
            else:
                self._expect(Symbol.Identifier)
                ret = Instruction_AddressOfVariable(self._lex.line_number, self._lex.current_identifier)
        elif function_name == "readkey":
            ret = Syscall_ReadKey(self._lex.line_number)
        elif function_name == "getrandomnumber":
            lower = self._parse_expression()
            self._expect(Symbol.Comma)
            upper = self._parse_expression()
            ret = Syscall_GetRandomNumber(self._lex.line_number, lower, upper)
        elif function_name == "consoleclear":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            ret = NonReturningSyscall(self._lex.line_number, "Std.ConsoleClear")
        elif function_name == "showconsolecursor":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            ret = NonReturningSyscall(self._lex.line_number, "Std.ShowConsoleCursor")
            ret.arg1 = self._parse_expression()
        elif function_name == "setconsolecursorposition":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            ret = NonReturningSyscall(self._lex.line_number, "Std.SetConsoleCursorPosition")
            ret.arg1 = self._parse_expression()
            self._expect(Symbol.Comma)
            ret.arg2 = self._parse_expression()
        elif function_name == "setconsolecolors":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            ret = NonReturningSyscall(self._lex.line_number, "Std.SetConsoleColors")
            ret.arg1 = self._parse_expression()
            self._expect(Symbol.Comma)
            ret.arg2 = self._parse_expression()
        elif function_name == "sleep":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            ret = NonReturningSyscall(self._lex.line_number, "Std.Sleep")
            ret.arg1 = self._parse_expression()
            ret.arg1_type = Type.Addr
        elif function_name == "readstring":
            if expected_return:
                self._error(f"Function {function_name} does not return and cannot be used in expression")
            ret = NonReturningSyscall(self._lex.line_number, "Std.ReadString")
            ret.arg1 = self._parse_expression()
            ret.arg1_type = Type.Addr
            self._expect(Symbol.Comma)
            ret.arg2 = self._parse_expression()
        else:
            self._error(f"Unknown function {function_name}")
        self._expect(Symbol.RParen)
        return ret

    def _parse_factor(self) -> AbstractExpression:
        if self._accept(Symbol.Hash):
            self._expect(Symbol.Number)
            return Number(self._lex.line_number, self._lex.current_number, Type.Addr)
        elif self._accept(Symbol.Identifier):
            var_name = self._lex.current_identifier

            if self._accept(Symbol.LParen):
                # Intrinsics that return value
                return self._parse_intrinsic(var_name, expected_return=True)

            constant = self.symbol_table.get_constant(self._current_context, var_name)
            if constant is not None:
                return ConstantUsage(self._lex.line_number, constant)

            var_def = self.symbol_table.get_variable(self._current_context, var_name)
            node = VariableUsageRHS(self._lex.line_number, var_def)

            if var_def.struct_def:
                last_var_in_chain, node = self._generate_struct_address(var_def, var_name, False)
                return node

            if self._accept(Symbol.LBracket):
                if not var_def.is_array:
                    self._error(f"Variable {var_name} is not an array!")

                if self._accept(Symbol.RBracket):
                    # arr[] is the same as arr[0]
                    node.array_jump = Number(self._lex.line_number, 0, Type.Addr)
                else:
                    expr = self._parse_expression()
                    self._expect(Symbol.RBracket)
                    node.array_jump = expr

            return node
        elif self._accept(Symbol.Number):
            number_type = Type.Byte if self._lex.current_number <= 255 else Type.Addr
            return Number(self._lex.line_number, self._lex.current_number, number_type)
        elif self._accept(Symbol.LParen):
            node = self._parse_sum()
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

            return Number(self._lex.line_number, ord(val), Type.Byte)

        elif self._accept(Symbol.Call):
            fcall = self._parse_function_call(inside_expression=True)
            if not isinstance(fcall, ReturningCall):
                self._error("Expected function returning value")
            return fcall

        else:
            self._error("factor: syntax error")

    def _parse_logical(self) -> AbstractExpression:
        node = self._parse_sum()
        while self._lex.current in (Symbol.Equals, Symbol.NotEqual, Symbol.Ge, Symbol.Gt, Symbol.Le, Symbol.Lt):
            v = self._lex.current
            self._lex.next_symbol()
            expr = self._parse_sum()
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
            node = LogicalOperation(self._lex.line_number, op)
            node.operand1 = old_node
            node.operand2 = expr
        return node

    def _parse_expression(self) -> AbstractExpression:
        return self._parse_logical_chain()

    def _parse_logical_chain(self) -> AbstractExpression:
        node = self._parse_logical()
        has_chain = False
        while self._lex.current in (Symbol.And, Symbol.Or):
            if self._accept(Symbol.Or):
                has_chain = True

                expr = self._parse_logical()
                old_node = node
                node = LogicalChainOperation(self._lex.line_number, BinOpType.LogicalOr, self._condition_counter)
                node.operand1 = old_node
                node.operand2 = expr

            elif self._accept(Symbol.And):
                has_chain = True

                expr = self._parse_logical()
                old_node = node
                node = LogicalChainOperation(self._lex.line_number, BinOpType.LogicalAnd, self._condition_counter)
                node.operand1 = old_node
                node.operand2 = expr

        if has_chain:
            self._condition_counter += 1
        return node

    def _parse_term(self) -> AbstractExpression:
        node = self._parse_factor()
        while self._lex.current in (
                Symbol.Mult, Symbol.Divide, Symbol.Modulo, Symbol.Ampersand, Symbol.Lsh, Symbol.Rsh):
            v = self._lex.current
            self._lex.next_symbol()
            node2 = self._parse_factor()

            old_node = node
            node = None

            if v == Symbol.Mult:
                op_ = BinOpType.Mul
                node = MultiplyOperation(self._lex.line_number)  # specialization important for constant folding
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
                node = BinaryOperation(self._lex.line_number, op_)
            node.operand1 = old_node
            node.operand2 = node2

        return node

    def _parse_sum(self) -> AbstractExpression:
        unary_minus = False
        negate = False

        if self._lex.current == Symbol.Minus:
            unary_minus = True
            self._lex.next_symbol()
        elif self._lex.current == Symbol.Tilde:
            negate = True
            self._lex.next_symbol()

        node = self._parse_term()

        if unary_minus:
            node = UnaryOperation(self._lex.line_number, UnOpType.UnaryMinus, node)
        if negate:
            node = UnaryOperation(self._lex.line_number, UnOpType.BitNegate, node)

        while self._lex.current in (Symbol.Plus, Symbol.Minus, Symbol.Pipe, Symbol.Hat):
            v = self._lex.current
            self._lex.next_symbol()
            node2 = self._parse_term()

            old_node = node
            node = None

            if v == Symbol.Plus:
                op_ = BinOpType.Add
                node = SumOperation(self._lex.line_number, )
            elif v == Symbol.Minus:
                op_ = BinOpType.Sub
                node = SubtractOperation(self._lex.line_number, )
            elif v == Symbol.Pipe:
                op_ = BinOpType.BitOr
            elif v == Symbol.Hat:
                op_ = BinOpType.BitXor
            else:
                raise NotImplementedError(v)

            if node is None:
                node = BinaryOperation(self._lex.line_number, op_)

            node.operand1 = old_node
            node.operand2 = node2
        return node

    def _generate_struct_address(self, var: Variable, var_name: str, is_lhs) -> (Variable, VariableUsage):
        """ Generates instructions to compute address of last member in struct chain
         Returns this last member variable """
        current_struct = var.struct_def
        if not current_struct:
            self._error("Expected structure")

        def create_vu(v: Variable):
            if is_lhs is None:
                return VariableUsageJustStructAddress(self._lex.line_number, v)
            elif is_lhs:
                return VariableUsageLHS(self._lex.line_number, v)
            else:
                return VariableUsageRHS(self._lex.line_number, var)

        ret = create_vu(var)
        if is_lhs is None:
            ret.generate_struct_load_store = False
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
                child_node = create_vu(var)
                if is_lhs is None:
                    child_node.generate_struct_load_store = False
                current_level.struct_child = child_node
                if var.struct_def:
                    current_struct = var.struct_def
                    current_level = child_node
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
                _, node = self._gen_array_initialization(var_name, var_type)
                self._expect(Symbol.Semicolon)
                return node
            else:
                var_def = self.symbol_table.register_variable(self._current_context, var_name, var_type)
                stmt = None
                if self._accept(Symbol.Becomes):  # initial value, like byte A = 1;
                    decl = VariableUsageLHS(self._lex.line_number, var_def)
                    val = self._parse_logical_chain()
                    stmt = Assign(self._lex.line_number, decl, val)
                self._expect(Symbol.Semicolon)
                return stmt

        elif self._lex.current == Symbol.Identifier and (
        struct_def := self.symbol_table.get_struct_definition(self._lex.current_identifier)):
            # struct init
            self._lex.next_symbol()
            self._expect(Symbol.Identifier)
            var_name = self._lex.current_identifier

            if self._accept(Symbol.LBracket):  # array of struct
                self._gen_array_initialization(var_name, struct_def=struct_def)
            elif self._accept(Symbol.Becomes):
                self._error("Cannot assign directly to structure")

            else:
                self.symbol_table.register_variable(self._current_context, var_name, Type.Struct, struct_def=struct_def)
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.Identifier):
            var_name = self._lex.current_identifier
            if self._accept(Symbol.LParen):
                # Non-returning intrinsics
                node = self._parse_intrinsic(var_name, expected_return=False)
                self._expect(Symbol.Semicolon)
                return node

            var = self.symbol_table.get_variable(self._current_context, var_name)
            if var.struct_def:
                # LHS structure element assignment
                last_var_in_chain, struct_node = self._generate_struct_address(var, var_name, True)

                self._expect(Symbol.Becomes)
                value = self._parse_expression()

                self._expect(Symbol.Semicolon)

                node = Assign(self._lex.line_number, struct_node, value)
                return node

            elif self._accept(Symbol.Becomes):
                # Simple LHS variable assignment
                node2 = self._parse_expression()
                self._expect(Symbol.Semicolon)

                node = Assign(self._lex.line_number, VariableUsageLHS(self._lex.line_number, self.symbol_table.get_variable(self._current_context, var_name)), node2)
                return node
            elif self._accept(Symbol.LBracket):
                # Array element LHS assignment
                var_def = self.symbol_table.get_variable(self._current_context, var_name)
                if not var_def.is_array:
                    self._error(f"Variable {var_name} is not an array")
                node = VariableUsageLHS(self._lex.line_number, var_def)
                element_size = var.type.size
                if self._accept(Symbol.RBracket):
                    # arr[] = the same as arr[0], no skip to calculate
                    node.array_jump = Number(self._lex.line_number, 0, Type.Addr)
                    self._expect(Symbol.Becomes)
                else:
                    jmp = self._parse_expression()
                    node.array_jump = jmp
                    self._expect(Symbol.RBracket)
                    self._expect(Symbol.Becomes)
                node2 = self._parse_expression()
                node = Assign(self._lex.line_number, node, node2)
                self._expect(Symbol.Semicolon)
                return node
        elif self._accept(Symbol.Global):
            if not inside_function:
                self._error("Global is allowed only inside functions!")
            self._expect(Symbol.Identifier)
            gvar = self.symbol_table.get_global_variable(self._lex.current_identifier)
            if gvar is None:
                self._error(f"Unknown global variable {self._lex.current_identifier}")
            self.symbol_table.register_variable(self._current_context, self._lex.current_identifier, gvar.type,
                                                is_array=gvar.is_array, from_global=True,
                                                struct_def=gvar.struct_def)
            self._expect(Symbol.Semicolon)

        elif self._accept(Symbol.Begin):
            stmt = GroupOfStatements(self._lex.line_number, [])
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
            cond = Condition(self._lex.line_number, no)
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

            node = WhileLoop(self._lex.line_number, no)

            expr = self._parse_expression()
            node.condition = expr

            self._expect(Symbol.Do)

            stmt = self._parse_statement(inside_loop=no, inside_if=inside_if, inside_function=inside_function)
            node.body = stmt

            return node

        elif self._accept(Symbol.Do):
            no = self._while_counter
            self._while_counter += 1
            node = DoWhileLoop(self._lex.line_number, no)

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
            return Instruction_Break(self._lex.line_number, inside_loop)

        elif self._accept(Symbol.Continue):
            self._expect(Symbol.Semicolon)
            if not inside_loop:
                self._error("Continue outside loop")
            return Instruction_Continue(self._lex.line_number, inside_loop)

        elif self._accept(Symbol.Call):
            return self._parse_function_call()

        elif self._accept(Symbol.Return):
            if not inside_function:
                self._error("Return outside function")

            if not self._accept(Symbol.Semicolon):
                expr = self._parse_expression()
                self._expect(Symbol.Semicolon)
                return FunctionReturn(self._lex.line_number, self.symbol_table.get_function_signature(self._current_context).return_value.type, expr)
            else:
                return FunctionReturn(self._lex.line_number, None, None)

        elif self._accept(Symbol.Print):
            if self._accept(Symbol.String):
                idx = self.symbol_table.get_index_of_string(self._lex.current_string)
                instr = Instruction_PrintStringConstant(self._lex.line_number, idx, self._lex.current_string)
            else:
                expr = self._parse_expression()
                instr = Instruction_PrintInteger(self._lex.line_number, expr)
            self._expect(Symbol.Semicolon)
            return instr

        elif self._accept(Symbol.PrintChar):
            expr = self._parse_sum()
            self._expect(Symbol.Semicolon)
            return Instruction_PrintChar(self._lex.line_number, expr)

        elif self._accept(Symbol.PrintStr):
            # print string from pointer
            expr = self._parse_expression()
            self._expect(Symbol.Semicolon)
            return Instruction_PrintStringByPointer(self._lex.line_number, expr)

        elif self._accept(Symbol.PrintNewLine):
            self._expect(Symbol.Semicolon)
            return Instruction_PrintNewLine(self._lex.line_number, )

        elif self._accept(Symbol.Debugger):
            self._expect(Symbol.Semicolon)
            return Instruction_Debugger(self._lex.line_number, )

        elif self._accept(Symbol.Halt):
            self._expect(Symbol.Semicolon)
            return Instruction_Halt(self._lex.line_number, )

        else:
            self._error("parse statement")

    def _parse_function_call(self, inside_expression=False) -> FunctionCall:
        self._expect(Symbol.Identifier)
        func = self._lex.current_identifier
        signature = self.symbol_table.get_function_signature(func)
        if signature is None:
            self._error(f"Unknown function {func}")

        self._expect(Symbol.LParen)

        return_value = signature.return_value

        if inside_expression and return_value is None:
            self._error(f"Function {func} does not return anything to be used in expression")

        node = FunctionCall(self._lex.line_number, func, signature) if not inside_expression else ReturningCall(self._lex.line_number, func, signature)

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
                _, node2 = self._generate_struct_address(self.symbol_table.get_variable(self._current_context, var_name), var_name, None)
                node.arguments.append(node2)
            else:
                self._expect(Symbol.Identifier)
                node.arguments.append(VariableUsageRHS(self._lex.line_number, self.symbol_table.get_variable(self._current_context, self._lex.current_identifier)))

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

                cdef = self.symbol_table.register_constant(self._current_context, const_name, const_type, const_value)
                self._expect(Symbol.Semicolon)

                return None
            else:
                self._error("Constant must be a simple type")
        elif self._accept(Symbol.Function):
            self._expect(Symbol.Identifier)
            old_ctx = self._current_context
            self._current_context = self._lex.current_identifier

            signature = FunctionSignature()
            self.symbol_table.register_function(self._current_context, signature)

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
                elif struct_def := self.symbol_table.get_struct_definition(self._lex.current_identifier):
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
                node = Function(self._lex.line_number, self._current_context, signature, body)
                node.scope = self._current_context
                self._current_context = old_ctx
                return node
            return None
        elif self._accept(Symbol.Struct):
            self._expect(Symbol.Identifier)
            struct_name = self._lex.current_identifier
            definition = StructDefinition(struct_name)
            self.symbol_table.register_struct(struct_name, definition)
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
                elif self._lex.current == Symbol.Identifier and (
                nested_struct := self.symbol_table.get_struct_definition(self._lex.current_identifier)):
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
                                       struct_def=nested_struct)
                        arg.array_fixed_size = size
                    else:
                        arg = Variable(var_name, Type.Struct, struct_def=nested_struct)
                    definition.members[var_name] = arg

                else:
                    self._error("Expected type")
            self._expect(Symbol.Semicolon)
        else:
            stmt = self._parse_statement(inside_function=inside_function)
            return stmt

    def do_parse(self) -> AstProgram:
        node = AstProgram(self._lex.line_number)
        self._lex.next_symbol()
        while not self._accept(Symbol.EOF):
            block = self._parse_block()
            if block:
                node.blocks.append(block)
        self._current_context = ""
        node.set_parents()
        node.symbol_table = self.symbol_table
        return node


if __name__ == '__main__':
    parser = Parser("""
addr a[10];
a[2] = a[0];
    """)
    tree = parser.do_parse()
    # tree.print(0)
    opt = True
    while opt:
        opt = tree.optimize()
    code = tree.gen_code(None)
    code.print()
    pass
