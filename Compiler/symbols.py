from enum import Enum
from typing import Optional, Dict, Sequence


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
    def __init__(self, name, type_: Type, by_ref: bool = False, is_array: bool = False, from_global: bool = False,
                 struct_def: Optional[StructDefinition] = None):
        """
        :param type_: In case of array its type of underlying elements, array itself is addr
        :param by_ref:
        :param is_array:
        :param from_global:
        """
        self.name = name
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
    def __init__(self, name, type_: Type, value: int):
        self.name = name
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
