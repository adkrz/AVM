from enum import Enum
from typing import List, Optional, Sequence, Iterable, TYPE_CHECKING

from codegen_helpers import CodeSnippet, generate_prolog, gen_load_store_instruction, _gen_address_of_str, offsetof, \
    _gen_address_of_variable
from optimizer import peephole_optimize
from symbols import Constant, FunctionSignature, Variable, Type

if TYPE_CHECKING:
    from symbol_table import SymbolTable


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


class AstNode:
    def __init__(self, line_no):
        self.line_no = line_no
        self._scope: Optional[str] = None  # if none, goes to parent
        self.parent: Optional["AstNode"] = None
        self._symbol_table: Optional["SymbolTable"] = None

    def set_parents(self, recursive=True):
        """ Recursively set parent relations starting from this node.
        This saves the hassle with manually setting parents on object construction / moving
         """
        for child in self.children():
            child.parent = self
            if recursive:
                child.set_parents()

    @property
    def scope(self) -> str:
        if self._scope is not None:
            return self._scope
        if self.parent is not None:
            return self.parent.scope
        return ""

    @scope.setter
    def scope(self, s: Optional[str]):
        self._scope = s

    @property
    def symbol_table(self) -> Optional["SymbolTable"]:
        if self._symbol_table is not None:
            return self._symbol_table
        if self.parent is not None:
            return self.parent.symbol_table
        return None

    @symbol_table.setter
    def symbol_table(self, s: Optional["SymbolTable"]):
        self._symbol_table = s

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
        self.set_parents()
        return opt


class AbstractBlock(AstNode):
    pass


class AbstractStatement(AbstractBlock):
    pass


class AbstractExpression(AstNode):
    @property
    def type(self) -> Optional[Type]:
        return None


class Dummy(AbstractExpression):
    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(self.line_no)


def highest_type(types: Iterable[Optional[Type]]) -> Type:
    ht = Type.Byte
    for t in types:
        if t == Type.Addr:
            ht = t
            break
    return ht


class BinaryOperation(AbstractExpression):
    def __init__(self, line_no, op: BinOpType):
        super().__init__(line_no)
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
            return CodeSnippet(self.line_no, "ADD" if target_type == Type.Byte else "ADD16", target_type)
        elif self.op == BinOpType.Sub:
            return CodeSnippet(self.line_no, "SUB2" if target_type == Type.Byte else "SUB216", target_type)
        elif self.op == BinOpType.Mul:
            return CodeSnippet(self.line_no, "MUL" if target_type == Type.Byte else "MUL16", target_type)
        elif self.op == BinOpType.Div:
            return CodeSnippet(self.line_no, "DIV2" if target_type == Type.Byte else "DIV216", target_type)
        elif self.op == BinOpType.Equals:
            return CodeSnippet(self.line_no, "EQ" if target_type == Type.Byte else "EQ16", target_type)
        elif self.op == BinOpType.NotEqual:
            return CodeSnippet(self.line_no, "NE" if target_type == Type.Byte else "NE16", target_type)
        elif self.op == BinOpType.Le:  # inverse because of order on stack
            return CodeSnippet(self.line_no, "GREATER_OR_EQ" if target_type == Type.Byte else "GREATER_OR_EQ16", target_type)
        elif self.op == BinOpType.Lt:
            return CodeSnippet(self.line_no, "GREATER" if target_type == Type.Byte else "GREATER16", target_type)
        elif self.op == BinOpType.Ge:
            return CodeSnippet(self.line_no, "LESS_OR_EQ" if target_type == Type.Byte else "LESS_OR_EQ16", target_type)
        elif self.op == BinOpType.Gt:
            return CodeSnippet(self.line_no, "LESS" if target_type == Type.Byte else "LESS16", target_type)
        elif self.op == BinOpType.BitAnd:
            return CodeSnippet(self.line_no, "AND" if target_type == Type.Byte else "AND16", target_type)
        elif self.op == BinOpType.BitOr:
            return CodeSnippet(self.line_no, "OR" if target_type == Type.Byte else "OR16", target_type)
        elif self.op == BinOpType.BitXor:
            return CodeSnippet(self.line_no, "XOR" if target_type == Type.Byte else "XOR16", target_type)
        elif self.op == BinOpType.Mod:
            cs = CodeSnippet(self.line_no, "SWAP" if target_type == Type.Byte else "SWAP16", target_type)
            cs.add_line("MOD" if target_type == Type.Byte else "MOD16")
            return cs
        elif self.op == BinOpType.Lsh:
            return CodeSnippet(self.line_no, "LSH" if target_type == Type.Byte else "LSH16", target_type)
        elif self.op == BinOpType.Rsh:
            return CodeSnippet(self.line_no, "RSH" if target_type == Type.Byte else "RSH16", target_type)

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.operand1:
            self.operand1 = new
        elif old == self.operand2:
            self.operand2 = new
        self.set_parents(False)

    def last_used_array(self) -> Optional["VariableUsageRHS"]:
        if isinstance(self.operand2, VariableUsageRHS) and self.operand2.definition.is_array:
            return self.operand2
        elif isinstance(self.operand1, VariableUsageRHS) and self.operand1.definition.is_array:
            return self.operand1
        return None

    @property
    def type(self) -> Optional[Type]:
        return highest_type((self.operand1.type, self.operand2.type))


class UnaryOperation(AbstractExpression):
    def __init__(self, line_no, op: UnOpType, operand: AbstractExpression):
        super().__init__(line_no)
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
            self.set_parents(False)

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c1 = self.operand.gen_code(type_hint)
        if self.op == UnOpType.BitNegate:
            c2 = CodeSnippet(self.line_no, "FLIP" if c1.type == Type.Byte else "FLIP16", c1.type)
            return CodeSnippet.join((c1, c2), c1.type)
        elif self.op == UnOpType.UnaryMinus:
            c2 = CodeSnippet(self.line_no, "NEG" if c1.type == Type.Byte else "NEG16", c1.type)
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
            self.parent.replace_child(self, CompareToZero(self.line_no, self.operand2, True))
            return True
        elif self.op == BinOpType.Equals and isinstance(self.operand2, Number) and self.operand2.is_zero:
            self.parent.replace_child(self, CompareToZero(self.line_no, self.operand1, True))
            return True
        if self.op == BinOpType.NotEqual and isinstance(self.operand1, Number) and self.operand1.is_zero:
            self.parent.replace_child(self, CompareToZero(self.line_no, self.operand2, False))
            return True
        elif self.op == BinOpType.NotEqual and isinstance(self.operand2, Number) and self.operand2.is_zero:
            self.parent.replace_child(self, CompareToZero(self.line_no, self.operand1, False))
            return True
        else:
            return super().optimize()


class CompareToZero(UnaryOperation):
    def __init__(self, line_no, expr: AbstractExpression, eq: bool):
        super().__init__(line_no, UnOpType.Other, expr)
        self.eq = eq

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c1 = self.operand.gen_code(type_hint)
        if self.eq:
            code = "ZERO" if c1.type == Type.Byte else "ZERO16"
        else:
            code = "NZERO" if c1.type == Type.Byte else "NZERO16"
        return CodeSnippet.join((c1, CodeSnippet(self.line_no, code, Type.Byte)), Type.Byte)  # logical ops are always 8bit

    def find_max_type(self) -> Optional[Type]:
        return Type.Byte

    @property
    def type(self) -> Optional[Type]:
        return Type.Byte


class SumOperation(BinaryOperation):
    def __init__(self, line_no):
        super().__init__(line_no, BinOpType.Add)

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
            self.parent.replace_child(self, AddConstant(self.line_no, self.operand2, self.operand1))
            return True
        elif isinstance(self.operand2, Number) and not isinstance(self.operand1, Number):
            self.parent.replace_child(self, AddConstant(self.line_no, self.operand1, self.operand2))
            return True
        else:
            return super().optimize()


class SubtractOperation(BinaryOperation):
    def __init__(self, line_no):
        super().__init__(line_no, BinOpType.Sub)

    def optimize(self) -> bool:
        if isinstance(self.operand1, Number) and isinstance(self.operand2, Number):
            new_node = self.operand1.combine(self.operand2, self.operand1.value - self.operand2.value)
            self.parent.replace_child(self, new_node)
            return True
        elif isinstance(self.operand1, Number) and self.operand1.is_zero:
            self.parent.replace_child(self, self.operand2)
            return True
        elif isinstance(self.operand2, Number) and self.operand2.is_zero:
            self.parent.replace_child(self, self.operand1)
            return True
        elif isinstance(self.operand1, Number) and not isinstance(self.operand2, Number):
            self.parent.replace_child(self, SubtractConstant(self.line_no, self.operand2, self.operand1))
            return True
        elif isinstance(self.operand2, Number) and not isinstance(self.operand1, Number):
            self.parent.replace_child(self, SubtractConstant(self.line_no, self.operand1, self.operand2))
            return True
        else:
            return super().optimize()


class AddConstant(UnaryOperation):
    def __init__(self, line_no, expr: AbstractExpression, value: "Number"):
        super().__init__(line_no, UnOpType.Other, expr)
        self.value = value

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        op_type = self.operand.type
        if isinstance(self.operand, VariableUsage):
            if self.operand.is_array and self.operand.array_jump is None:
                op_type = Type.Addr
        target_type = highest_type((type_hint, op_type))
        c1 = self.operand.gen_code(target_type)
        c1.cast(target_type)
        if self.value.is_one:
            c2 = CodeSnippet(self.line_no, "INC" if target_type == Type.Byte else "INC16", target_type)
        else:
            c2 = CodeSnippet(self.line_no,
                f"ADDC {self.value.value}" if target_type == Type.Byte else f"ADD16C #{self.value.value}",
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
        self.set_parents(False)

    def optimize(self) -> bool:
        if isinstance(self.operand, Number):
            self.parent.replace_child(self, self.operand.combine(self.value, self.operand.value + self.value.value))
            return True
        else:
            return super().optimize()


class SubtractConstant(UnaryOperation):
    def __init__(self, line_no, expr: AbstractExpression, value: "Number"):
        super().__init__(line_no, UnOpType.Other, expr)
        self.value = value

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        op_type = self.operand.type
        if isinstance(self.operand, VariableUsage):
            if self.operand.is_array and self.operand.array_jump is None:
                op_type = Type.Addr
        target_type = highest_type((type_hint, op_type))
        c1 = self.operand.gen_code(target_type)
        c1.cast(target_type)
        if self.value.is_one:
            c2 = CodeSnippet(self.line_no, "DEC" if target_type == Type.Byte else "DEC16", target_type)
        else:
            c2 = CodeSnippet(self.line_no,
                f"SUBC {self.value.value}" if target_type == Type.Byte else f"SUB16C #{self.value.value}",
                target_type)
        return CodeSnippet.join((c1, c2), target_type)

    @property
    def is_decrement(self):
        return self.value.is_one

    def children(self):
        yield self.value
        yield self.operand

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if self.value == old:
            self.value = new
        if self.operand == old:
            self.operand = new
        self.set_parents(False)

    def optimize(self) -> bool:
        if isinstance(self.operand, Number):
            self.parent.replace_child(self, self.operand.combine(self.value, self.operand.value - self.value.value))
            return True
        else:
            return super().optimize()


class MulConstant(UnaryOperation):
    def __init__(self, line_no, expr: AbstractExpression, value: "Number"):
        super().__init__(line_no, UnOpType.Other, expr)
        self.value = value

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        target_type = highest_type((type_hint, self.operand.type))
        c1 = self.operand.gen_code(target_type)
        c1.cast(target_type)
        if self.value.value == 2:
            c2 = CodeSnippet(self.line_no, "MACRO_X2" if target_type == Type.Byte else "MACRO_X216", target_type)
        else:
            c2 = CodeSnippet(self.line_no,
                f"MULC {self.value.value}" if target_type == Type.Byte else f"MUL16C #{self.value.value}",
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
        self.set_parents(False)

    def optimize(self) -> bool:
        if isinstance(self.operand, Number):
            self.parent.replace_child(self, self.operand.combine(self.value, self.operand.value * self.value.value))
            return True
        else:
            return super().optimize()


class MultiplyOperation(BinaryOperation):
    def __init__(self, line_no):
        super().__init__(line_no, BinOpType.Mul)

    def optimize(self) -> bool:
        if isinstance(self.operand1, Number) and isinstance(self.operand2, Number):
            new_node = self.operand1.combine(self.operand2, self.operand1.value * self.operand2.value)
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
            self.parent.replace_child(self, Number(self.line_no, 0, self.type))
            return True
        elif isinstance(self.operand1, Number) and not isinstance(self.operand2, Number):
            self.parent.replace_child(self, MulConstant(self.line_no, self.operand2, self.operand1))
            return True
        elif isinstance(self.operand2, Number) and not isinstance(self.operand1, Number):
            self.parent.replace_child(self, MulConstant(self.line_no, self.operand1, self.operand2))
            return True
        else:
            return super().optimize()


class DivisionOperation(BinaryOperation):
    def __init__(self, line_no):
        super().__init__(line_no, BinOpType.Div)

    def optimize(self) -> bool:
        if isinstance(self.operand2, Number) and self.operand2.is_zero:
            raise ValueError(f"Division by zero detected in line {self.line_no}")
        if isinstance(self.operand1, Number) and isinstance(self.operand2, Number):
            new_node = self.operand1.combine(self.operand2, int(self.operand1.value / self.operand2.value))
            self.parent.replace_child(self, new_node)
            return True
        elif isinstance(self.operand1, Number) and self.operand1.is_zero:
            self.parent.replace_child(self, self.operand1)
            return True
        else:
            return super().optimize()


class LogicalChainOperation(BinaryOperation):  # AND, OR
    def __init__(self, line_no, op, condition_counter):
        super().__init__(line_no, op)
        self.condition_counter = condition_counter

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        jmp = "JT" if self.op == BinOpType.LogicalOr else "JF"
        comp2 = "OR" if self.op == BinOpType.LogicalOr else "AND"
        c1 = self.operand1.gen_code(type_hint)
        suffix = "" if c1.type == Type.Byte else "16"
        code_dup = f"DUP{suffix}"
        code_jmp = f"{jmp}{suffix} @cond{self.condition_counter}_expr_end"
        c2 = CodeSnippet(self.line_no, code_dup)
        c2.add_line(code_jmp)
        c3 = self.operand2.gen_code(type_hint)
        c3.add_line(comp2 + suffix)
        if self.parent and not isinstance(self.parent, LogicalChainOperation):
            c3.add_line(f":cond{self.condition_counter}_expr_end")
        return CodeSnippet.join((c1, c2, c3), self.type)

    @property
    def type(self) -> Optional[Type]:
        return highest_type((self.operand1.type, self.operand2.type))


class Number(AbstractExpression):
    def __init__(self, line_no, value, type_: Type):
        super().__init__(line_no)
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
                sn = CodeSnippet(self.line_no, f"PUSH16 #{self.value}", Type.Addr)
            else:
                sn = CodeSnippet(self.line_no, f"PUSH {self.value}", Type.Byte)
        else:
            if type_hint == Type.Byte:
                val = self.value if self.value <= 255 else 255
                sn = CodeSnippet(self.line_no, f"PUSH {val}", Type.Byte)
            else:
                sn = CodeSnippet(self.line_no, f"PUSH16 #{self.value}", Type.Addr)
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
        const_node = Number(self.line_no, new_value, resulting_type)
        return const_node


class ConstantUsage(Number):
    def __init__(self, line_no, cdef: Constant):
        self.cdef = cdef
        super().__init__(line_no, self.cdef.value, self.cdef.type)

    @property
    def name(self):
        return self.cdef.name

    def print(self, lvl):
        self._print_indented(lvl, self.type.name + " " + str(self.value) + f" (const {self.cdef.name})")


class StoreAtPointer(AbstractExpression):
    def __init__(self, line_no, type_: Type):
        super().__init__(line_no)
        self.type_ = type_

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(self.line_no, "STORE_GLOBAL_PTR" if self.type_ == Type.Byte else "STORE_GLOBAL_PTR16")

    @property
    def type(self) -> Optional[Type]:
        return self.type_

    @property
    def is_array(self):
        return True

    @property
    def array_jump(self):
        return None


class Assign(AbstractStatement):
    def __init__(self, line_no, var: "VariableUsageLHS", value: AbstractExpression):
        super().__init__(line_no)
        self.var = var
        self.value = value

    @property
    def type(self):
        return self.var.type

    def print(self, lvl):
        self.var.print(lvl + 1)
        self._print_indented(lvl, "=")
        self.value.print(lvl + 1)

    def children(self):
        yield self.value
        yield self.var

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        if self.var.is_array and self.var.array_jump is None:
            # direct ptr address assignment
            c1 = self.value.gen_code(None)
            c2 = self.var.gen_code(self.type)
            snippet = CodeSnippet.join((c1, c2), self.type)
            return snippet

        max_type = highest_type((type_hint, self.value.find_max_type(), self.var.last_type()))
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
        self.set_parents(True)  # should be recursive there

    def optimize(self) -> bool:
        if (isinstance(self.value, AddConstant)
                and self.value.is_increment
                and isinstance(self.value.operand, VariableUsage)
                and isinstance(self.var, VariableUsageLHS)
                and self.var.definition == self.value.operand.definition
                and (not self.var.definition.is_array or self.var.definition.is_array and not self.var.array_jump)
                and not self.var.definition.struct_def
                and not self.var.definition.is_arg
                and not self.var.definition.from_global
        ):
            self.parent.replace_child(self, IncLocal(self.line_no, self.var))
            return True
        elif (isinstance(self.value, SubtractConstant)
              and self.value.is_decrement
              and isinstance(self.value.operand, VariableUsage)
              and isinstance(self.var, VariableUsageLHS)
              and self.var.definition == self.value.operand.definition
              and (not self.var.definition.is_array or self.var.definition.is_array and not self.var.array_jump)
              and not self.var.definition.struct_def
              and not self.var.definition.is_arg
              and not self.var.definition.from_global
        ):
            self.parent.replace_child(self, DecLocal(self.line_no, self.var))
            return True
        elif (isinstance(self.value, Number)
              and not self.var.definition.is_array
              and not self.var.definition.struct_def
              and not self.var.definition.is_arg
              and not self.var.definition.from_global
        ):
            self.parent.replace_child(self, SetLocal(self.line_no, self.var, self.value.value))
            return True
        elif (isinstance(self.var, VariableUsageLHS)
              and isinstance(self.value, VariableUsageRHS)
              and self.var.definition == self.value.definition
              and self.var.array_jump == self.value.array_jump
              and self.var.struct_child == self.value.struct_child):
            # a = a
            self.parent.replace_child(self, None)
            return True
        elif (isinstance(self.var, VariableUsageLHS)
              and self.var.definition.is_array
              and self.var.array_jump
              and isinstance(self.value, BinaryOperation)
              and (var := self.value.last_used_array())):
            if var.definition == self.var.definition:
                # compare array access code, except last line (load/store global)
                left_code = self.var.gen_code(None)
                right_code = var.gen_code(None)
                if len(left_code.codes) == len(right_code.codes):
                    code_equal = True
                    for left, right in zip(left_code.codes[:-1], right_code.codes[:-1]):
                        if left != right:
                            code_equal = False
                            break
                    if code_equal:
                        self.var = StoreAtPointer(self.line_no, self.var.definition.type)
                        self.var.parent = self
                        return True
            return super().optimize()

        else:
            return super().optimize()


class IncLocal(AbstractStatement):
    def __init__(self, line_no, var: "VariableUsageLHS"):
        super().__init__(line_no)
        self.var = var

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        offs = offsetof(self.symbol_table, self.scope, self.var.name, False)
        vtype = self.var.definition.type if not self.var.is_array else Type.Addr
        instr = self._instr(vtype)
        return CodeSnippet(self.line_no,
            f"{instr} {offs} ;{self.var.name}", self.var.definition.type)

    def _instr(self, type):
        return "MACRO_INC_LOCAL" if type == Type.Byte else f"MACRO_INC_LOCAL16"


class DecLocal(IncLocal):
    def _instr(self, type):
        return "MACRO_DEC_LOCAL" if type == Type.Byte else f"MACRO_DEC_LOCAL16"


class SetLocal(AbstractStatement):
    def __init__(self, line_no, var: "VariableUsageLHS", constant_value):
        super().__init__(line_no)
        self.var = var
        self.value = constant_value

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        offs = offsetof(self.symbol_table, self.scope, self.var.name, False)
        vtype = self.var.definition.type if not self.var.is_array else Type.Addr
        instr = f"MACRO_SET_LOCAL {offs} {self.value}" if vtype == Type.Byte else f"MACRO_SET_LOCAL16 {offs} #{self.value}"
        return CodeSnippet(self.line_no,
            f"{instr} ;{self.var.name}", self.var.definition.type)


class VariableUsage(AbstractStatement):
    def __init__(self, line_no, definition: Variable):
        super().__init__(line_no)
        self.definition = definition
        self.array_jump: Optional[AbstractExpression] = None
        self.struct_child: Optional[VariableUsage] = None
        self._processed_array_jump = None

    @property
    def name(self):
        return self.definition.name

    @property
    def type(self):
        if self.definition.is_array and not self.array_jump:  # simple pointer
            return Type.Addr
        return self.definition.type

    def last_type(self):
        """ In case of structs, returns last element type, otherwise just variable element type """
        if self.struct_child:
            return self.struct_child.last_type()
        return self.type

    @property
    def is_load(self):
        raise NotImplementedError()

    def _gen_struct_load_store(self):
        """ Generate the final load/store after struct address, or not? """
        return True

    @property
    def is_array(self):
        return self.definition.is_array

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
        if self._processed_array_jump:
            yield self._processed_array_jump

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.array_jump:
            self.array_jump = new
        if old == self.struct_child:
            self.struct_child = new
        if old == self._processed_array_jump:
            self._processed_array_jump = new
        self.set_parents(False)

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        if self.definition.struct_def:
            member_offset = 0
            if not self.definition.is_arg:
                base_address = _gen_address_of_variable(self.line_no, self.symbol_table, self.scope, self.name)
            else:
                base_address = gen_load_store_instruction(self.line_no, self.symbol_table, self.scope, self.definition.name, True)
            snippets = [base_address]
            current_level = self
            while 1:
                if current_level.array_jump:
                    if isinstance(current_level.array_jump, Number):
                        member_offset += current_level.array_jump.value * current_level.definition.struct_def.stack_size
                    else:
                        index_var = current_level.array_jump.gen_code(Type.Addr)
                        index_var.cast(Type.Addr)
                        snippets.append(index_var)
                        if current_level.definition.struct_def.stack_size > 1:
                            snippets.append(CodeSnippet(self.line_no, f"MUL16C #{current_level.definition.stack_size_single_element}", Type.Addr))
                        snippets.append(CodeSnippet(self.line_no, "ADD16", Type.Addr))
                if current_level.struct_child:
                    member_offset += current_level.definition.struct_def.member_offset(current_level.struct_child.name)
                    current_level = current_level.struct_child
                else:
                    last_var_type = current_level.type
                    break
            if member_offset > 0:
                snippets.append(CodeSnippet(self.line_no, f"ADD16C #{member_offset}"))

            if self._gen_struct_load_store():
                suffix = "" if last_var_type == Type.Byte else "16"
                snippets.append(CodeSnippet(self.line_no, f"LOAD_GLOBAL{suffix}" if self.is_load else f"STORE_GLOBAL{suffix}"))

            return CodeSnippet.join(snippets, last_var_type)

        if not self.array_jump:
            code = gen_load_store_instruction(self.line_no, self.symbol_table, self.scope, self.definition.name, self.is_load)
            if self.definition.is_array:  # read address of pointer
                code.type = Type.Addr
            else:
                code.type = self.definition.type
            return code
        # else: calculate address
        c1 = gen_load_store_instruction(self.line_no, self.symbol_table, self.scope, self.definition.name, True)
        if self.array_jump:
            element_size = 1 if self.definition.type == Type.Byte else 2

            # Create internally sum+multiply objects and exploit optimization functions to them:
            self._processed_array_jump = SumOperation(self.line_no)
            self._processed_array_jump.parent = self
            self._processed_array_jump.operand1 = Dummy(self.line_no)
            if element_size > 1:
                self._processed_array_jump.operand2 = MulConstant(self.line_no, self.array_jump, Number(self.line_no, element_size, Type.Addr))
            else:
                self._processed_array_jump.operand2 = self.array_jump
            self._processed_array_jump.set_parents()
            opt = True
            while opt:
                opt = self._processed_array_jump.optimize()

            if isinstance(self._processed_array_jump, Number) and self._processed_array_jump.is_zero:
                self._processed_array_jump = None

            if self._processed_array_jump:
                c2 = self._processed_array_jump.gen_code(Type.Addr)
                c1 = CodeSnippet.join((c1, c2), Type.Addr)
        if self.is_load:
            c1.add_line("LOAD_GLOBAL" if self.definition.type == Type.Byte else "LOAD_GLOBAL16")
        else:
            c1.add_line("STORE_GLOBAL" if self.definition.type == Type.Byte else "STORE_GLOBAL16")
        c1.type = self.definition.type
        return c1


class VariableUsageLHS(VariableUsage):
    @property
    def is_load(self):
        return False


class VariableUsageRHS(VariableUsageLHS, AbstractExpression):
    @property
    def is_load(self):
        return True


class VariableUsageJustStructAddress(VariableUsage):
    @property
    def is_load(self):
        return True

    def _gen_struct_load_store(self):
        return False


class GroupOfStatements(AbstractStatement):
    def __init__(self, line_no, statements: List[AbstractStatement]):
        super().__init__(line_no)
        self.statements = statements

    def print(self, lvl):
        for s in self.statements:
            s.print(lvl + 1)

    def children(self):
        yield from self.statements

    def replace_child(self, old: "AstNode", new: "AstNode"):
        for i, s in enumerate(self.statements):
            if s == old:
                self.statements[i] = new
                self.set_parents(False)
                break

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        codes = [s.gen_code(type_hint) for s in self.statements]
        return CodeSnippet.join(codes)


class Function(AbstractBlock):
    def __init__(self, line_no, name, signature: FunctionSignature, body: AbstractBlock):
        super().__init__(line_no)
        self.name = name
        self.body = body
        self.signature = signature

    def print(self, lvl):
        self._print_indented(lvl, f"Function {self.name}")
        self.body.print(lvl + 1)

    def children(self):
        yield self.body

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.body:
            self.body = new
        self.set_parents(False)

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        snippet1 = CodeSnippet(self.line_no, f":function_{self.name}\n;{self.signature}")
        snippet2 = generate_prolog(self.line_no, self.symbol_table, self.name)
        snippet3 = self.body.gen_code(None)
        if snippet3.codes and snippet3.codes[-1] != "RET":
            snippet3.add_line("RET")
        return CodeSnippet.join((snippet1, snippet2, snippet3))


class Condition(AbstractStatement):
    def __init__(self, line_no, number: int):
        super().__init__(line_no)
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

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.condition:
            self.condition = new
        elif old == self.if_body:
            self.if_body = new
        elif old == self.else_body:
            self.else_body = new
        self.set_parents(False)

    def optimize(self) -> bool:
        if isinstance(self.condition, Number):
            if self.condition.is_zero:
                if self.else_body:
                    self.parent.replace_child(self, self.else_body)
                    return True
                else:
                    self.parent.replace_child(self, None)
                    return True
            else:
                self.parent.replace_child(self, self.if_body)
                return True
        return super().optimize()

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        snippet1 = self.condition.gen_code(self.condition.type)
        if self.else_body:
            snippet2 = CodeSnippet(self.line_no,
                f"JF @if{self.number}_else" if self.condition.type == Type.Byte else f"JF16 @if{self.number}_else")
        else:
            snippet2 = CodeSnippet(self.line_no,
                f"JF @if{self.number}_endif" if self.condition.type == Type.Byte else f"JF16 @if{self.number}_endif")
        snippet3 = self.if_body.gen_code(type_hint)
        if self.else_body:
            snippet3.add_line(f"JMP @if{self.number}_endif")
        snippets = [snippet1, snippet2, snippet3]

        if self.else_body:
            snippet3.add_line(f":if{self.number}_else")
            snippet4 = self.else_body.gen_code(type_hint)
            snippets.append(snippet4)
        ret = CodeSnippet.join(snippets, type_hint)
        ret.add_line(f":if{self.number}_endif")
        return ret


class WhileLoop(AbstractStatement):
    def __init__(self, line_no, number: int):
        super().__init__(line_no)
        self.number = number
        self.condition: AbstractExpression = None
        self.body: AbstractStatement = None
        self._is_infinite = False

    def print(self, lvl):
        self._print_indented(lvl, f"while:")
        self.condition.print(lvl + 1)
        self._print_indented(lvl, f"body:")
        self.body.print(lvl + 1)

    def children(self):
        yield self.condition
        yield self.body

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.condition:
            self.condition = new
        elif old == self.body:
            self.body = new
        self.set_parents(False)

    def optimize(self) -> bool:
        if isinstance(self.condition, Number):
            if self.condition.is_zero:
                self.parent.replace_child(self, None)
                return True
            else:
                self.condition = Dummy(self.line_no)
                self.condition.set_parents(False)
                return False
        return super().optimize()

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        snippet1 = CodeSnippet(self.line_no, f":while{self.number}_begin")
        snippet2 = self.condition.gen_code(self.condition.type)
        if not isinstance(self.condition, Dummy):
            snippet3 = CodeSnippet(self.line_no,
                f"JF @while{self.number}_endwhile" if self.condition.type == Type.Byte else f"JF16 @while{self.number}_endwhile")
        else:
            snippet3 = CodeSnippet(self.line_no)
        snippet4 = self.body.gen_code(type_hint)
        snippet4.add_line(f"JMP @while{self.number}_begin")
        snippet4.add_line(f":while{self.number}_endwhile")
        return CodeSnippet.join((snippet1, snippet2, snippet3, snippet4))


class DoWhileLoop(AbstractStatement):
    def __init__(self, line_no, number: int):
        super().__init__(line_no)
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

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.condition:
            self.condition = new
        elif old == self.body:
            self.body = new
        self.set_parents(False)

    def optimize(self) -> bool:
        if isinstance(self.condition, Number):
            if self.condition.is_zero:
                self.parent.replace_child(self, self.body)
                return True
        return super().optimize()

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        snippet1 = CodeSnippet(self.line_no, f":while{self.number}_begin")
        snippet2 = self.body.gen_code(type_hint)
        snippet3 = self.condition.gen_code(self.condition.type)
        snippet4 = CodeSnippet(self.line_no,
            f"JT @while{self.number}_begin" if self.condition.type == Type.Byte else f"JT16 @while{self.number}_begin")
        snippet4.add_line(f":while{self.number}_endwhile")
        return CodeSnippet.join((snippet1, snippet2, snippet3, snippet4))


class Instruction_PrintStringConstant(AbstractStatement):
    def __init__(self, line_no, string_number: int, content: str):
        super().__init__(line_no)
        self.string_number = string_number
        self.content = content

    def print(self, lvl):
        self._print_indented(lvl, f"print string {self.string_number} \"{self.content}\"")

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c1 = _gen_address_of_str(self.line_no, self.symbol_table, self.content)
        c1.add_line("SYSCALL Std.PrintString")
        return c1


class Instruction_PrintStringByPointer(AbstractStatement):
    def __init__(self, line_no, expr: AbstractExpression):
        super().__init__(line_no)
        self.expr = expr

    def print(self, lvl):
        self._print_indented(lvl, f"print string ptr")
        self.expr.print(lvl + 1)

    def children(self):
        yield self.expr

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.expr:
            self.expr = new
            self.set_parents(False)

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c1 = self.expr.gen_code(Type.Addr)
        c1.cast(Type.Addr)
        c1.add_line("SYSCALL Std.PrintString")
        return c1


class Instruction_PrintInteger(AbstractStatement):
    def __init__(self, line_no, expr: AbstractExpression):
        super().__init__(line_no)
        self.expr = expr

    def print(self, lvl):
        self._print_indented(lvl, "print int")
        self.expr.print(lvl + 1)

    def children(self):
        yield self.expr

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c = self.expr.gen_code(type_hint)
        if c.type == Type.Byte or c.type is None:
            c.add_line("SYSCALL Std.PrintInt")
            c.add_line("POP")
        else:
            c.add_line("SYSCALL Std.PrintInt16")
            c.add_line("POPN 2")
        return c

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.expr:
            self.expr = new
            self.set_parents(False)


class Instruction_PrintChar(AbstractStatement):
    def __init__(self, line_no, expr: AbstractExpression):
        super().__init__(line_no)
        self.expr = expr

    def print(self, lvl):
        self._print_indented(lvl, "print char")
        self.expr.print(lvl + 1)

    def children(self):
        yield self.expr

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.expr:
            self.expr = new
            self.set_parents(False)

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c = self.expr.gen_code(Type.Byte)
        c.cast(Type.Byte)
        c.add_line("SYSCALL Std.PrintCharPop")
        return c


class Instruction_PrintNewLine(AbstractStatement):
    def print(self, lvl):
        self._print_indented(lvl, "newline")

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(self.line_no, "SYSCALL Std.PrintNewLine")


class Instruction_Halt(AbstractStatement):
    def print(self, lvl):
        self._print_indented(lvl, "halt")

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(self.line_no, "HALT")


class Instruction_Debugger(AbstractStatement):
    def print(self, lvl):
        self._print_indented(lvl, "debugger")

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(self.line_no, "debugger")


class Instruction_Continue(AbstractStatement):
    def __init__(self, line_no, loop_no):
        super().__init__(line_no)
        self.loop_no = loop_no

    def print(self, lvl):
        self._print_indented(lvl, "continue")

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(self.line_no, f"JMP @while{self.loop_no}_begin")


class Instruction_Break(AbstractStatement):
    def __init__(self, line_no, loop_no):
        super().__init__(line_no)
        self.loop_no = loop_no

    def print(self, lvl):
        self._print_indented(lvl, "break")

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(self.line_no, f"JMP @while{self.loop_no}_endwhile")


class FunctionCall(AbstractStatement):
    def __init__(self, line_no, name: str, signature: FunctionSignature):
        super().__init__(line_no)
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
                self.set_parents(False)
                break

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        snippets = []

        return_value = self.signature.return_value

        if self.signature.return_value:
            s = CodeSnippet(self.line_no, "PUSH 0 ; rv" if not return_value.is_16bit else "PUSHN 2 ; rv")
            snippets.append(s)

        refs_mapping = {}

        for arg, arg_def in zip(self.arguments, self.signature.true_args):
            s = arg.gen_code(arg_def.type)
            adt = arg_def.type
            if isinstance(arg_def, Variable) and arg_def.is_array:
                adt = Type.Addr
            s.cast(adt)
            if arg_def.by_ref or arg_def.is_array:
                if not isinstance(arg, (VariableUsageRHS, VariableUsageJustStructAddress)):
                    raise RuntimeError("Reference target must be simple variable")
                refs_mapping[arg_def] = arg.name
            snippets.append(s)

        snippets.append(CodeSnippet(self.line_no, f"CALL @function_{self.name}"))

        pop_count = 0
        for name, arg in reversed(self.signature.args.items()):
            if not arg.by_ref and not arg.struct_def:
                pop_count += arg.stack_size
            elif arg.struct_def:
                pop_count += 2
            else:
                if arg == return_value and self.clean_return_value():
                    pop_count += 1 if not return_value.is_16bit else 2

                if pop_count > 0:
                    snippets.append(CodeSnippet(self.line_no, f"POPN {pop_count}"))
                    pop_count = 0
                if arg != return_value:
                    snippets.append(gen_load_store_instruction(self.line_no, self.symbol_table, self.scope, refs_mapping[arg], False))

        if pop_count > 0:
            snippets.append(CodeSnippet(self.line_no, f"POPN {pop_count}"))

        return CodeSnippet.join(snippets)

    def clean_return_value(self) -> bool:
        return True


class FunctionReturn(AbstractStatement):
    def __init__(self, line_no, return_type: Type, value: Optional[AbstractExpression]):
        super().__init__(line_no)
        self.return_type = return_type
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
            self.set_parents(False)

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        if self.value is None:
            return CodeSnippet(self.line_no, "RET")
        snippet1 = self.value.gen_code(self.return_type)
        snippet1.cast(self.return_type)
        snippet2 = gen_load_store_instruction(self.line_no, self.symbol_table, self.scope, FunctionSignature.RETURN_VALUE_NAME, False)
        snippet2.add_line("RET")
        return CodeSnippet.join((snippet1, snippet2), self.return_type)


class ReturningCall(FunctionCall, AbstractExpression):
    def _type(self):
        return "CALL_WITH_RET"

    def clean_return_value(self) -> bool:
        return False  # keep RV on stack to use in expression


class ArrayInitializationStatement(AbstractStatement):
    def __init__(self, line_no, definition: Variable):
        super().__init__(line_no)
        self.definition = definition


class ArrayInitialization_StackAlloc(ArrayInitializationStatement):
    def __init__(self, line_no, definition: Variable, length: AbstractExpression):
        super().__init__(line_no, definition)
        self.length = length

    def print(self, lvl):
        self._print_indented(lvl, "Array init stack:")
        self.length.print(lvl + 1)

    def children(self):
        yield self.length

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.length:
            self.length = new
            self.set_parents(False)

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c1 = CodeSnippet(self.line_no, "PUSH_REG 1")
        c2 = gen_load_store_instruction(self.line_no, self.symbol_table, self.scope, self.definition.name, False)
        c3 = self.length.gen_code(type_hint)
        c3.cast(Type.Byte)  # limitation of PUSHN2
        if self.definition.type == Type.Addr:
            if isinstance(self.length, Number):
                tmp = Number(self.line_no,  self.length.value * 2, Type.Byte)
                c3 = tmp.gen_code(Type.Byte)
            else:
                c3.add_line("MULC 2")
        return CodeSnippet.join((c1, c2, c3, CodeSnippet(self.line_no, "PUSHN2")))

    def optimize(self) -> bool:
        if isinstance(self.length, Number) and self.length.is_zero:
            self.parent.replace_child(self, None)
            return True
        else:
            return super().optimize()


class ArrayInitialization_InitializerList(ArrayInitializationStatement):
    def __init__(self, line_no, definition: Variable):
        super().__init__(line_no, definition)
        self.elements: List[Number] = []

    def print(self, lvl):
        self._print_indented(lvl, "Array init by initializer list:")
        self._print_indented(lvl, " ".join(str(e) for e in self.elements))

    def children(self):
        yield from self.elements

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        stack_pos = CodeSnippet(self.line_no, "PUSH_REG 1", type_=self.definition.type)
        store = gen_load_store_instruction(self.line_no, self.symbol_table, self.scope, self.definition.name, False)
        numbers = [n.gen_code(type_hint) for n in self.elements]
        return CodeSnippet.join([stack_pos, store] + numbers, self.definition.type)


class ArrayInitialization_Pointer(ArrayInitializationStatement):
    def __init__(self, line_no, definition: Variable, pointer: AbstractExpression):
        super().__init__(line_no, definition)
        self.pointer = pointer

    def print(self, lvl):
        self._print_indented(lvl, "Array init by ptr:")
        self.pointer.print(lvl + 1)

    def children(self):
        yield self.pointer

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.pointer:
            self.pointer = new
            self.set_parents(False)

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c1 = self.pointer.gen_code(Type.Addr)
        c1.cast(Type.Addr)
        c2 = gen_load_store_instruction(self.line_no, self.symbol_table, self.scope, self.definition.name, False)
        return CodeSnippet.join((c1, c2), Type.Addr)


class Instruction_AddressOfString(AbstractExpression):
    def __init__(self, line_no, string: str):
        super().__init__(line_no)
        self.string = string

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return _gen_address_of_str(self.line_no, self.symbol_table, self.string)

    @property
    def type(self) -> Optional[Type]:
        return Type.Addr


class Instruction_AddressOfVariable(AbstractExpression):
    def __init__(self, line_no, name: str):
        super().__init__(line_no)
        self.name = name

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return _gen_address_of_variable(self.line_no, self.symbol_table, self.scope, self.name)

    @property
    def type(self) -> Optional[Type]:
        return Type.Addr


class Syscall_GetRandomNumber(AbstractExpression):
    def __init__(self, line_no, lower: AbstractExpression, upper: AbstractExpression):
        super().__init__(line_no)
        self.lower = lower
        self.upper = upper

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        c1 = self.lower.gen_code(Type.Byte)
        c1.cast(Type.Byte)
        c2 = self.upper.gen_code(Type.Byte)
        c2.cast(Type.Byte)
        c3 = CodeSnippet(self.line_no, "SYSCALL Std.GetRandomNumber", Type.Byte)
        return CodeSnippet.join((c1, c2, c3), Type.Byte)

    @property
    def type(self) -> Optional[Type]:
        return Type.Byte

    def children(self) -> Sequence["AstNode"]:
        yield self.lower
        yield self.upper

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.lower:
            self.lower = new
        if old == self.upper:
            self.upper = new
        self.set_parents(False)


class Syscall_ReadKey(AbstractExpression):
    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        return CodeSnippet(self.line_no, "SYSCALL Std.ReadKey", Type.Byte)

    @property
    def type(self) -> Optional[Type]:
        return Type.Byte


class NonReturningSyscall(AbstractExpression):
    def __init__(self, line_no, call_name):
        super().__init__(line_no)
        self.arg1: Optional[AbstractExpression] = None
        self.arg2: Optional[AbstractExpression] = None
        self.arg1_type = Type.Byte
        self.arg2_type = Type.Byte
        self.call_name = call_name

    def gen_code(self, type_hint: Optional[Type]) -> Optional[CodeSnippet]:
        codes = []
        if self.arg1 is not None:
            c1 = self.arg1.gen_code(self.arg1_type)
            codes.append(c1)

        if self.arg2 is not None:
            c2 = self.arg2.gen_code(self.arg2_type)
            codes.append(c2)

        codes.append(CodeSnippet(self.line_no, f"SYSCALL {self.call_name}"))
        return CodeSnippet.join(codes)

    def children(self) -> Sequence["AstNode"]:
        if self.arg1:
            yield self.arg1
        if self.arg2:
            yield self.arg2

    def replace_child(self, old: "AstNode", new: "AstNode"):
        if old == self.arg1:
            self.arg1 = new
        if old == self.arg2:
            self.arg2 = new
        self.set_parents(False)


class AstProgram(AstNode):
    def __init__(self, line_no):
        super().__init__(line_no)
        self.blocks: List[AbstractBlock] = []

    def print(self, lvl):
        for b in self.blocks:
            b.print(lvl + 1)

    def children(self):
        yield from self.blocks

    def gen_code(self, optimize_assembly=True) -> Optional[CodeSnippet]:
        # Move functions to the end:
        blocks_functions = [b for b in self.blocks if isinstance(b, Function)]
        blocks_main = [b for b in self.blocks if not isinstance(b, Function)]

        blocks = [b.gen_code(None) for b in blocks_main]
        program_prolog = generate_prolog(self.line_no, self.symbol_table, "")
        blocks.insert(0, program_prolog)
        blocks.append(CodeSnippet(self.line_no, "HALT"))
        main_block = CodeSnippet.join(blocks)

        blocks = [main_block]

        blocks += [b.gen_code(None) for b in blocks_functions]

        if optimize_assembly:
            for code in blocks:
                peephole_optimize(code)

        ret = CodeSnippet.join(blocks)

        for i, stc in enumerate(self.symbol_table.get_all_strings()):
            ret.add_line(f":string_{i + 1}")
            ret.add_line(f"\"{stc}\"")

        return ret

    def replace_child(self, old: "AstNode", new: "AstNode"):
        for i, block in enumerate(self.blocks):
            if block == old:
                if new is not None:
                    self.blocks[i] = new
                    self.set_parents(False)
                else:
                    del self.blocks[i]
                break
