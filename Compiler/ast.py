from enum import Enum
from typing import List, Optional, Tuple, Sequence

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


class AstNode:
    def print(self, lvl):
        pass

    @staticmethod
    def _print_indented(lvl, text):
        print(" " * lvl + str(text))

    def children(self) -> Sequence["AstNode"]:
        return []

    def gen_code(self):
        for child in self.children():
            child.gen_code()


class AbstractBlock(AstNode):
    pass


class AbstractStatement(AbstractBlock):
    pass


class AbstractExpression(AstNode):
    pass


class BinaryOperation(AbstractExpression):
    def __init__(self, op: BinOpType):
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


class UnaryOperation(AbstractExpression):
    def __init__(self, op: UnOpType, operand: AstNode):
        self.op = op
        self.operand = operand

    def print(self, lvl):
        self._print_indented(lvl, f"[{self.op.name}]:")
        self.operand.print(lvl + 1)

    def children(self):
        yield self.operand


class LogicalOperation(BinaryOperation):  # eq, less etc
    pass


class SumOperation(BinaryOperation):
    pass


class MultiplyOperation(BinaryOperation):
    pass


class LogicalChainOperation(BinaryOperation):  # AND, OR
    pass


class Number(AbstractExpression):
    def __init__(self, value, type_: Type):
        self.value = value
        self.type = type_

    def print(self, lvl):
        self._print_indented(lvl, self.type.name + " " + str(self.value))


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
        self.var = var
        self.value = value

    def print(self, lvl):
        self.var.print(lvl + 1)
        self._print_indented(lvl, "=")
        self.value.print(lvl + 1)

    def children(self):
        yield self.value
        yield self.var


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


class VariableUsageLHS(VariableUsage):
    pass


class VariableUsageRHS(VariableUsageLHS, AbstractExpression):
    pass


class GroupOfStatements(AbstractStatement):
    def __init__(self, statements: List[AbstractStatement]):
        self.statements = statements

    def print(self, lvl):
        for s in self.statements:
            s.print(lvl + 1)

    def children(self):
        yield from self.statements


class Function(AbstractBlock):
    def __init__(self, name, signature: FunctionSignature, body: AbstractBlock):
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
        self.string_number = string_number
        self.content = content

    def print(self, lvl):
        self._print_indented(lvl, f"print string {self.string_number} \"{self.content}\"")


class Instruction_PrintStringByPointer(AbstractStatement):
    def __init__(self, expr: AbstractExpression):
        self.expr = expr

    def print(self, lvl):
        self._print_indented(lvl, f"print string ptr")
        self.expr.print(lvl + 1)

    def children(self):
        yield self.expr


class Instruction_PrintInteger(AbstractStatement):
    def __init__(self, expr: AbstractExpression):
        self.expr = expr

    def print(self, lvl):
        self._print_indented(lvl, "print int")
        self.expr.print(lvl + 1)

    def children(self):
        yield self.expr


class Instruction_PrintChar(AbstractStatement):
    def __init__(self, expr: AbstractExpression):
        self.expr = expr

    def print(self, lvl):
        self._print_indented(lvl, "print char")
        self.expr.print(lvl + 1)

    def children(self):
        yield self.expr


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


class FunctionReturn(AbstractStatement):
    def __init__(self, value: Optional[AbstractExpression]):
        self.value = value

    def print(self, lvl):
        self._print_indented(lvl, f"RETURN")
        if self.value:
            self.value.print(lvl + 1)

    def children(self):
        if self.value:
            yield self.value


class ReturningCall(FunctionCall, AbstractExpression):
    def _type(self):
        return "CALL_WITH_RET"


class ArrayInitializationStatement(AbstractStatement):
    def __init__(self, definition: Variable):
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


class AstProgram(AstNode):
    def __init__(self):
        self.blocks: List[AbstractBlock] = []

    def print(self, lvl):
        for b in self.blocks:
            b.print(lvl + 1)

    def children(self):
        yield from self.blocks
