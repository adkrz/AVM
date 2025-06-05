from enum import Enum
from typing import List, Optional, Sequence, Iterable

from symbols import Constant, FunctionSignature, Variable, Type


class BinOpType(Enum):
    Add = 1
    Sub = 2
    Mul = 3
    Div = 4
    Equals = 5
    NotEqual = 6
    Ge = 7
    Gt = 8
    Le = 9
    Lt = 10
    BitAnd = 11
    BitOr = 12
    BitXor = 13
    Mod = 14
    Lsh = 15
    Rsh = 16
    LogicalAnd = 17
    LogicalOr = 18


class UnOpType(Enum):
    UnaryMinus = 1
    BitNegate = 2
    Other = 3  # e.g. for operation on immediate constants, that inherit from unary


class CodeSnippet:
    def __init__(self, code: str = "", type_: Optional[Type] = None):
        self.type = type_
        self.codes: List[str] = [code] if code else []

    def add_line(self, line):
        self.codes.append(line)

    def print(self):
        for c in self.codes:
            print(c)

    @staticmethod
    def join(snippets: Iterable[Optional["CodeSnippet"]], type_: Optional[Type] = None) -> "CodeSnippet":
        ret = CodeSnippet(type_=type_)
        for sn in snippets:
            if sn:
                for code in sn.codes:
                    ret.codes.append(code)
        return ret

    def cast(self, expected_type: Optional[Type]):
        if expected_type is None:
            return
        if self.type == Type.Byte and expected_type == Type.Addr:
            self.add_line("EXTEND")
        elif self.type == Type.Addr and expected_type == Type.Byte:
            self.add_line("DOWNCAST")


class AstNode:
    def __init__(self):
        self._scope: Optional[str] = None  # if none, goes to parent
        self.parent: Optional["AstNode"] = None

    def set_parents(self):
        """ Recursively set parent relations starting from this node.
        This saves the hassle with manually setting parents on object construction / moving
         """
        for child in self.children():
            child.parent = self
            child.set_parents()

    @property
    def scope(self) -> str:
        if self._scope is not None:
            return self.scope
        if self.parent is not None:
            return self.parent.scope
        return ""

    @scope.setter
    def scope(self, s: Optional[str]):
        self._scope = s

    def print(self, lvl):
        pass

    @staticmethod
    def _print_indented(lvl, text):
        print(" " * lvl + str(text))

    def children(self) -> Sequence["AstNode"]:
        return []

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return None

    def find_max_type(self) -> Optional[Type]:
        return None

    def replace_child(self, old: "AstNode", new: "AstNode"):
        raise NotImplementedError(f"Replace not implemented in {self.__class__.__name__}")

    def optimize(self) -> bool:
        opt = False
        for child in self.children():
            o = child.optimize()
            if o:
                opt = o
        return opt


class AbstractBlock(AstNode):
    pass


class AbstractStatement(AbstractBlock):
    pass


class AbstractExpression(AstNode):
    @property
    def type(self) -> Optional[Type]:
        return None


def highest_type(types: Iterable[Optional[Type]]) -> Type:
    ht = Type.Byte
    for t in types:
        if t == Type.Addr:
            ht = t
            break
    return ht


class BinaryOperation(AbstractExpression):
    def __init__(self, op: BinOpType):
        super().__init__()
        self.op = op
        self.operand1: AbstractExpression = None
        self.operand2: AbstractExpression = None

    def print(self, lvl):
        self._print_indented(lvl, f"[{self.op.name}]:")
        self.operand1.print(lvl + 1)
        self.operand2.print(lvl + 1)

    def children(self):
        yield self.operand1
        yield self.operand2

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        target_type = highest_type((type_hint, self.operand1.type, self.operand2.type))
        c1 = self.operand1.gen_code(target_type)
        c2 = self.operand2.gen_code(target_type)
        c1.cast(target_type)
        c2.cast(target_type)
        c3 = self._gen_operation_code(target_type)
        return CodeSnippet.join((c1, c2, c3), target_type)

    def find_max_type(self) -> Optional[Type]:
        return highest_type((self.operand1.find_max_type(), self.operand2.find_max_type()))

    def _gen_operation_code(self, target_type) -> CodeSnippet:
        if self.op == BinOpType.Add:
            return CodeSnippet("ADD" if target_type == Type.Byte else "ADD16", target_type)
        elif self.op == BinOpType.Sub:
            return CodeSnippet("SUB2" if target_type == Type.Byte else "SUB216", target_type)
        elif self.op == BinOpType.Mul:
            return CodeSnippet("MUL" if target_type == Type.Byte else "MUL16", target_type)
        elif self.op == BinOpType.Div:
            return CodeSnippet("DIV2" if target_type == Type.Byte else "DIV16", target_type)
        elif self.op == BinOpType.Equals:
            return CodeSnippet("EQ" if target_type == Type.Byte else "EQ16", target_type)
        elif self.op == BinOpType.NotEqual:
            return CodeSnippet("NE" if target_type == Type.Byte else "NE16", target_type)
        elif self.op == BinOpType.Le:  # inverse because of order on stack
            return CodeSnippet("GREATER_OR_EQ" if target_type == Type.Byte else "GREATER_OR_EQ16", target_type)
        elif self.op == BinOpType.Lt:
            return CodeSnippet("GREATER" if target_type == Type.Byte else "GREATER16", target_type)
        elif self.op == BinOpType.Ge:
            return CodeSnippet("LESS_OR_EQ" if target_type == Type.Byte else "LESS_OR_EQ16", target_type)
        elif self.op == BinOpType.Gt:
            return CodeSnippet("LESS" if target_type == Type.Byte else "LESS16", target_type)
        elif self.op == BinOpType.BitAnd:
            return CodeSnippet("AND" if target_type == Type.Byte else "AND16", target_type)
        elif self.op == BinOpType.BitOr:
            return CodeSnippet("OR" if target_type == Type.Byte else "OR16", target_type)
        elif self.op == BinOpType.BitXor:
            return CodeSnippet("XOR" if target_type == Type.Byte else "XOR16", target_type)
        elif self.op == BinOpType.Mod:
            cs = CodeSnippet("SWAP" if target_type == Type.Byte else "SWAP16", target_type)
            cs.add_line("MOD" if target_type == Type.Byte else "MOD16")
        elif self.op == BinOpType.Lsh:
            return CodeSnippet("LSH" if target_type == Type.Byte else "LSH16", target_type)
        elif self.op == BinOpType.Rsh:
            return CodeSnippet("RSH" if target_type == Type.Byte else "RSH16", target_type)

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.operand1:
            self.operand1 = new
        elif old == self.operand2:
            self.operand2 = new
        self.set_parents(False)


class UnaryOperation(AbstractExpression):
    def __init__(self, op: UnOpType, operand: AbstractExpression):
        super().__init__()
        self.op = op
        self.operand = operand

    def print(self, lvl):
        self._print_indented(lvl, f"[{self.op.name}]:")
        self.operand.print(lvl + 1)

    def children(self):
        yield self.operand

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.operand:
            self.operand = new

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c1 = self.operand.gen_code(type_hint)
        if self.op == UnOpType.BitNegate:
            c2 = CodeSnippet("FLIP" if c1.type == Type.Byte else "FLIP16", c1.type)
            return CodeSnippet.join((c1, c2), c1.type)
        elif self.op == UnOpType.UnaryMinus:
            c2 = CodeSnippet("NEG" if c1.type == Type.Byte else "NEG16", c1.type)
            return CodeSnippet.join((c1, c2), c1.type)
        return c1

    def find_max_type(self) -> Optional[Type]:
        return self.operand.type


class LogicalOperation(BinaryOperation):  # eq, less etc
    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        target_type = highest_type((self.operand1.type, self.operand2.type))
        c1 = self.operand1.gen_code(target_type)
        c2 = self.operand2.gen_code(target_type)
        c1.cast(target_type)
        c2.cast(target_type)
        c3 = self._gen_operation_code(target_type)
        return CodeSnippet.join((c1, c2, c3), Type.Byte)  # logical ops are always 8bit

    def find_max_type(self) -> Optional[Type]:
        return Type.Byte

    @property
    def type(self) -> Optional[Type]:
        return Type.Byte

    def optimize(self) -> bool:
        def _replace_with_bool(bool_val):
            self.parent.replace_child(self, Number(1 if bool_val else 0, Type.Byte))
            return True

        if isinstance(self.operand1, Number) and isinstance(self.operand2, Number):
            if self.op == BinOpType.Equals:
                return _replace_with_bool(self.operand1.value == self.operand2.value)
            elif self.op == BinOpType.NotEqual:
                return _replace_with_bool(self.operand1.value != self.operand2.value)
            elif self.op == BinOpType.Gt:
                return _replace_with_bool(self.operand1.value > self.operand2.value)
            elif self.op == BinOpType.Ge:
                return _replace_with_bool(self.operand1.value >= self.operand2.value)
            elif self.op == BinOpType.Lt:
                return _replace_with_bool(self.operand1.value < self.operand2.value)
            elif self.op == BinOpType.Le:
                return _replace_with_bool(self.operand1.value <= self.operand2.value)
        if self.op == BinOpType.Equals and isinstance(self.operand1, Number) and self.operand1.is_zero:
            self.parent.replace_child(self, CompareToZero(self.operand2, True))
            return True
        elif self.op == BinOpType.Equals and isinstance(self.operand2, Number) and self.operand2.is_zero:
            self.parent.replace_child(self, CompareToZero(self.operand1, True))
            return True
        if self.op == BinOpType.NotEqual and isinstance(self.operand1, Number) and self.operand1.is_zero:
            self.parent.replace_child(self, CompareToZero(self.operand2, False))
            return True
        elif self.op == BinOpType.NotEqual and isinstance(self.operand2, Number) and self.operand2.is_zero:
            self.parent.replace_child(self, CompareToZero(self.operand1, False))
            return True
        else:
            return super().optimize()


class CompareToZero(UnaryOperation):
    def __init__(self, expr: AbstractExpression, eq: bool):
        super().__init__(UnOpType.Other, expr)
        self.eq = eq

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c1 = self.operand.gen_code(type_hint)
        if self.eq:
            code = "ZERO" if c1.type == Type.Byte else "ZERO16"
        else:
            code = "NZERO" if c1.type == Type.Byte else "NZERO16"
        return CodeSnippet.join((c1, CodeSnippet(code, Type.Byte)), Type.Byte)  # logical ops are always 8bit

    def find_max_type(self) -> Optional[Type]:
        return Type.Byte


class SumOperation(BinaryOperation):
    def optimize(self) -> bool:
        if isinstance(self.operand1, Number) and isinstance(self.operand2, Number):
            new_node = self.operand1.combine(self.operand2, self.operand1.value + self.operand2.value)
            self.parent.replace_child(self, new_node)
            return True
        elif isinstance(self.operand1, Number) and self.operand1.is_zero:
            self.parent.replace_child(self, self.operand2)
            return True
        elif isinstance(self.operand2, Number) and self.operand2.is_zero:
            self.parent.replace_child(self, self.operand1)
            return True
        elif isinstance(self.operand1, Number) and not isinstance(self.operand2, Number):
            self.parent.replace_child(self, AddConstant(self.operand2, self.operand1))
            return True
        elif isinstance(self.operand2, Number) and not isinstance(self.operand1, Number):
            self.parent.replace_child(self, AddConstant(self.operand1, self.operand2))
            return True
        else:
            return super().optimize()


class AddConstant(UnaryOperation):
    def __init__(self, expr: AbstractExpression, value: "Number"):
        super().__init__(UnOpType.Other, expr)
        self.value = value

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        target_type = highest_type((type_hint, self.operand.type))
        c1 = self.operand.gen_code(target_type)
        c1.cast(target_type)
        if self.value.is_one:
            c2 = CodeSnippet("INC" if self.value.type == Type.Byte else "INC16", target_type)
        else:
            c2 = CodeSnippet(
                f"ADDC {self.value.value}" if self.value.type == Type.Byte else f"ADD16C #{self.value.value}",
                target_type)
        return CodeSnippet.join((c1, c2), target_type)

    @property
    def is_increment(self):
        return self.value.is_one

    def children(self):
        yield self.value
        yield self.operand

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if self.value == old:
            self.value = new
        if self.operand == old:
            self.operand = new

    def optimize(self) -> bool:
        if isinstance(self.operand, Number):
            self.parent.replace_child(self, self.operand.combine(self.value, self.operand.value + self.value.value))
            return True
        else:
            return super().optimize()


class MulConstant(UnaryOperation):
    def __init__(self, expr: AbstractExpression, value: "Number"):
        super().__init__(UnOpType.Other, expr)
        self.value = value

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        target_type = highest_type((type_hint, self.operand.type))
        c1 = self.operand.gen_code(target_type)
        c1.cast(target_type)
        if self.value.value == 2:
            c2 = CodeSnippet("MACRO_X2" if self.value.type == Type.Byte else "MACRO_X216", target_type)
        else:
            c2 = CodeSnippet(
                f"MULC {self.value.value}" if self.value.type == Type.Byte else f"MUL16C #{self.value.value}",
                target_type)
        return CodeSnippet.join((c1, c2), target_type)

    @property
    def is_increment(self):
        return self.value.is_one

    def children(self):
        yield self.value
        yield self.operand

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if self.value == old:
            self.value = new
        if self.operand == old:
            self.operand = new

    def optimize(self) -> bool:
        if isinstance(self.operand, Number):
            self.parent.replace_child(self, self.operand.combine(self.value, self.operand.value * self.value.value))
            return True
        else:
            return super().optimize()


class MultiplyOperation(BinaryOperation):

    def optimize(self) -> bool:
        if isinstance(self.operand1, Number) and isinstance(self.operand2, Number):
            new_node = self.operand1.combine(self.operand2, self.operand1.value + self.operand2.value)
            self.parent.replace_child(self, new_node)
            return True
        elif isinstance(self.operand1, Number) and self.operand1.is_one:
            self.parent.replace_child(self, self.operand2)
            return True
        elif isinstance(self.operand2, Number) and self.operand2.is_one:
            self.parent.replace_child(self, self.operand1)
            return True
        elif (isinstance(self.operand1, Number) and self.operand1.is_zero) or (
                isinstance(self.operand2, Number) and self.operand2.is_zero):
            self.parent.replace_child(self, Number(0, self.type))
            return True
        elif isinstance(self.operand1, Number) and not isinstance(self.operand2, Number):
            self.parent.replace_child(self, MulConstant(self.operand2, self.operand1))
            return True
        elif isinstance(self.operand2, Number) and not isinstance(self.operand1, Number):
            self.parent.replace_child(self, MulConstant(self.operand1, self.operand2))
            return True
        else:
            return super().optimize()


class LogicalChainOperation(BinaryOperation):  # AND, OR
    pass


class Number(AbstractExpression):
    def __init__(self, value, type_: Type):
        super().__init__()
        self.value = value
        self._type = type_

    def print(self, lvl):
        self._print_indented(lvl, self.type.name + " " + str(self.value))

    @property
    def type(self) -> Optional[Type]:
        return self._type

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        if self.type == Type.Byte:
            if type_hint == Type.Addr:
                sn = CodeSnippet(f"PUSH16 #{self.value}", Type.Addr)
            else:
                sn = CodeSnippet(f"PUSH {self.value}", Type.Byte)
        else:
            if type_hint == Type.Byte:
                val = self.value if self.value <= 255 else 255
                sn = CodeSnippet(f"PUSH {val}", Type.Byte)
            else:
                sn = CodeSnippet(f"PUSH16 #{self.value}", Type.Addr)
        return sn

    def find_max_type(self) -> Optional[Type]:
        return self._type

    @property
    def is_zero(self):
        return self.value == 0

    @property
    def is_one(self):
        return self.value == 1

    def combine(self, another: "Number", new_value) -> "Number":
        resulting_type = highest_type((self.type, another.type))
        if new_value > 255:
            resulting_type = Type.Addr
        const_node = Number(new_value, resulting_type)
        return const_node


class ConstantUsage(Number):
    def __init__(self, cdef: Constant):
        self.cdef = cdef
        super().__init__(self.cdef.value, self.cdef.type)

    @property
    def name(self):
        return self.cdef.name

    def print(self, lvl):
        self._print_indented(lvl, self.type.name + " " + str(self.value) + f" (const {self.cdef.name})")


class Assign(AbstractStatement):
    def __init__(self, var: "VariableUsageLHS", value: AbstractExpression):
        super().__init__()
        self.var = var
        self.value = value

    @property
    def type(self):
        return self.var.definition.type

    def print(self, lvl):
        self.var.print(lvl + 1)
        self._print_indented(lvl, "=")
        self.value.print(lvl + 1)

    def children(self):
        yield self.value
        yield self.var

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        max_type = highest_type((type_hint, self.value.find_max_type(), self.type))
        c1 = self.value.gen_code(max_type)
        c1.cast(self.type)
        c2 = self.var.gen_code(self.type)
        snippet = CodeSnippet.join((c1, c2), self.type)
        return snippet

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.value:
            self.value = new
        if old == self.var:
            self.var = new

    def optimize(self) -> bool:
        if (isinstance(self.value, AddConstant)
                and self.value.is_increment
                and isinstance(self.value.operand, VariableUsage)
                and self.var.definition == self.value.operand.definition
                and not self.var.definition.is_array
                and not self.var.definition.struct_def
        ):
            self.parent.replace_child(self, IncLocal(self.var))
            return True
        elif isinstance(self.var, VariableUsageLHS) and isinstance(self.value,
                                                                   VariableUsageRHS) and self.var.definition == self.value.definition:
            # a = a
            self.parent.replace_child(self, None)
            return True
        else:
            return self.value.optimize()


class IncLocal(AbstractStatement):
    def __init__(self, var: "VariableUsageLHS"):
        super().__init__()
        self.var = var

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(
            f"INC_LOCAL {self.var.name}" if self.var.definition.type == Type.Byte else f"INC_LOCAL16 {self.var.name}",
            self.var.definition.type)


class VariableUsage(AbstractStatement):
    def __init__(self, definition: Variable):
        super().__init__()
        self.definition = definition
        self.array_jump: Optional[AbstractExpression] = None
        self.struct_child: Optional[VariableUsage] = None

    @property
    def name(self):
        return self.definition.name

    def print(self, lvl):
        self._print_indented(lvl, f"Variable {self.definition.name} : {self.definition.type.name}")
        if self.array_jump is not None:
            self._print_indented(lvl + 1, "array offset:")
            self.array_jump.print(lvl + 1)
        if self.struct_child is not None:
            self._print_indented(lvl + 1, "struct child:")
            self.struct_child.print(lvl + 1)

    def children(self):
        if self.array_jump:
            yield self.array_jump
        if self.struct_child:
            yield self.struct_child

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.array_jump:
            self.array_jump = new
        if old == self.struct_child:
            self.struct_child = new


class VariableUsageLHS(VariableUsage):
    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(f"STORE {self.definition.name}", self.definition.type)


class VariableUsageRHS(VariableUsageLHS, AbstractExpression):
    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(f"LOAD {self.definition.name}", self.definition.type)


class GroupOfStatements(AbstractStatement):
    def __init__(self, statements: List[AbstractStatement]):
        super().__init__()
        self.statements = statements

    def print(self, lvl):
        for s in self.statements:
            s.print(lvl + 1)

    def children(self):
        yield from self.statements


class Function(AbstractBlock):
    def __init__(self, name, signature: FunctionSignature, body: AbstractBlock):
        super().__init__()
        self.name = name
        self.body = body
        self.signature = signature

    def print(self, lvl):
        self._print_indented(lvl, f"Function {self.name}")
        self.body.print(lvl + 1)

    def children(self):
        yield self.body


class Condition(AbstractStatement):
    def __init__(self, number: int):
        super().__init__()
        self.number = number
        self.condition: AbstractExpression = None
        self.if_body: AbstractStatement = None
        self.else_body: AbstractStatement = None

    def print(self, lvl):
        self._print_indented(lvl, f"if:")
        self.condition.print(lvl + 1)
        self._print_indented(lvl, f"then:")
        self.if_body.print(lvl + 1)
        if self.else_body:
            self._print_indented(lvl, f"else:")
            self.else_body.print(lvl + 1)

    def children(self):
        yield self.condition
        yield self.if_body
        if self.else_body:
            yield self.else_body


class WhileLoop(AbstractStatement):
    def __init__(self, number: int):
        super().__init__()
        self.number = number
        self.condition: AbstractExpression = None
        self.body: AbstractStatement = None

    def print(self, lvl):
        self._print_indented(lvl, f"while:")
        self.condition.print(lvl + 1)
        self._print_indented(lvl, f"body:")
        self.body.print(lvl + 1)

    def children(self):
        yield self.condition
        yield self.body


class DoWhileLoop(AbstractStatement):
    def __init__(self, number: int):
        super().__init__()
        self.number = number
        self.condition: AbstractExpression = None
        self.body: AbstractStatement = None

    def print(self, lvl):
        self._print_indented(lvl, f"dowhile:")
        self.condition.print(lvl + 1)
        self._print_indented(lvl, f"body:")
        self.body.print(lvl + 1)

    def children(self):
        yield self.condition
        yield self.body


class Instruction_PrintStringConstant(AbstractStatement):
    def __init__(self, string_number: int, content: str):
        super().__init__()
        self.string_number = string_number
        self.content = content

    def print(self, lvl):
        self._print_indented(lvl, f"print string {self.string_number} \"{self.content}\"")


class Instruction_PrintStringByPointer(AbstractStatement):
    def __init__(self, expr: AbstractExpression):
        super().__init__()
        self.expr = expr

    def print(self, lvl):
        self._print_indented(lvl, f"print string ptr")
        self.expr.print(lvl + 1)

    def children(self):
        yield self.expr

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.expr:
            self.expr = new


class Instruction_PrintInteger(AbstractStatement):
    def __init__(self, expr: AbstractExpression):
        super().__init__()
        self.expr = expr

    def print(self, lvl):
        self._print_indented(lvl, "print int")
        self.expr.print(lvl + 1)

    def children(self):
        yield self.expr

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c = self.expr.gen_code(type_hint)
        if c.type == Type.Byte:
            c.add_line("Printint")
        else:
            c.add_line("Printint16")
        return c

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.expr:
            self.expr = new


class Instruction_PrintChar(AbstractStatement):
    def __init__(self, expr: AbstractExpression):
        super().__init__()
        self.expr = expr

    def print(self, lvl):
        self._print_indented(lvl, "print char")
        self.expr.print(lvl + 1)

    def children(self):
        yield self.expr

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.expr:
            self.expr = new


class Instruction_PrintNewLine(AbstractStatement):
    def print(self, lvl):
        self._print_indented(lvl, "newline")


class Instruction_Halt(AbstractStatement):
    def print(self, lvl):
        self._print_indented(lvl, "halt")


class Instruction_Debugger(AbstractStatement):
    def print(self, lvl):
        self._print_indented(lvl, "debugger")


class Instruction_Continue(AbstractStatement):
    def print(self, lvl):
        self._print_indented(lvl, "continue")


class Instruction_Break(AbstractStatement):
    def print(self, lvl):
        self._print_indented(lvl, "break")


class FunctionCall(AbstractStatement):
    def __init__(self, name: str, signature: FunctionSignature):
        super().__init__()
        self.name = name
        self.signature = signature
        self.arguments: List[AbstractExpression] = []

    def _type(self):
        return "CALL"

    def print(self, lvl):
        self._print_indented(lvl, f"{self._type()} {self.name}")
        for arg in self.arguments:
            arg.print(lvl + 1)

    def children(self):
        yield from self.arguments

    def replace_child(self, old: "AstNode", new: "AstNode"):
        for i, arg in enumerate(self.arguments):
            if arg == old:
                self.arguments[i] = new
                break


class FunctionReturn(AbstractStatement):
    def __init__(self, value: Optional[AbstractExpression]):
        super().__init__()
        self.value = value

    def print(self, lvl):
        self._print_indented(lvl, f"RETURN")
        if self.value:
            self.value.print(lvl + 1)

    def children(self):
        if self.value:
            yield self.value

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.value:
            self.value = new


class ReturningCall(FunctionCall, AbstractExpression):
    def _type(self):
        return "CALL_WITH_RET"


class ArrayInitializationStatement(AbstractStatement):
    def __init__(self, definition: Variable):
        super().__init__()
        self.definition = definition


class ArrayInitialization_StackAlloc(ArrayInitializationStatement):
    def __init__(self, definition: Variable, length: AbstractExpression):
        super().__init__(definition)
        self.length = length

    def print(self, lvl):
        self._print_indented(lvl, "Array init stack:")
        self.length.print(lvl + 1)

    def children(self):
        yield self.length

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.length:
            self.length = new

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c1 = self.length.gen_code(type_hint)
        c1.cast(Type.Byte)  # limitation of PUSHN2
        return CodeSnippet.join((c1, CodeSnippet("PUSHN2")))

    def optimize(self) -> bool:
        if isinstance(self.length, Number) and self.length.is_zero:
            self.parent.replace_child(self, None)
            return True
        else:
            super().optimize()


class ArrayInitialization_InitializerList(ArrayInitializationStatement):
    def __init__(self, definition: Variable):
        super().__init__(definition)
        self.elements: List[Number] = []

    def print(self, lvl):
        self._print_indented(lvl, "Array init by initializer list:")
        self._print_indented(lvl, " ".join(str(e) for e in self.elements))

    def children(self):
        yield from self.elements


class ArrayInitialization_Pointer(ArrayInitializationStatement):
    def __init__(self, definition: Variable, pointer: AbstractExpression):
        super().__init__(definition)
        self.pointer = pointer

    def print(self, lvl):
        self._print_indented(lvl, "Array init by ptr:")
        self.pointer.print(lvl + 1)

    def children(self):
        yield self.pointer

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.pointer:
            self.pointer = new


class AstProgram(AstNode):
    def __init__(self):
        super().__init__()
        self.blocks: List[AbstractBlock] = []

    def print(self, lvl):
        for b in self.blocks:
            b.print(lvl + 1)

    def children(self):
        yield from self.blocks

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet.join(b.gen_code(type_hint) for b in self.blocks)

    def replace_child(self, old: "AstNode", new: "AstNode"):
        for i, block in enumerate(self.blocks):
            if block == old:
                if new is not None:
                    self.blocks[i] = new
                else:
                    del self.blocks[i]
                break
