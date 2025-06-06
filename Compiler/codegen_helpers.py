from typing import Optional, List, Iterable

from symbol_table import SymbolTable
from symbols import Type


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


def generate_prolog(symbol_table: SymbolTable, function_name: str) -> CodeSnippet:
    ret = CodeSnippet()
    vars = symbol_table.get_all_variables(function_name)
    if not vars:
        return ret
    total_stack_size = 0
    for k, var in vars.items():
        if not var.from_global:
            name = k
            if var.is_array:
                name += "[]"
            if var.struct_def and not var.is_array:
                total_stack_size += var.stack_size
                ret.add_line(f"; struct {var.struct_def.name} {name}")
            else:
                if var.is_array and var.array_fixed_size == 0:
                    # pointer
                    total_stack_size += 2
                else:
                    # normal variable or array of known size from initializer list
                    total_stack_size += var.stack_size
                ret.add_line(f"; {var.type.name} {name}")
    # todo: initial value instead of just push
    if total_stack_size > 0:
        ret.add_line(f"PUSHN {total_stack_size}")
    return ret


def gen_load_store_instruction(symbol_table: SymbolTable, scope, name: str, load: bool) -> CodeSnippet:
    def gen(offset, is_arg, is_16bit):
        instr = "LOAD" if load else "STORE"
        bbits = "16" if is_16bit else ""
        origin = "ARG" if is_arg else "LOCAL"
        code = f"{instr}_{origin}{bbits} {offset} ; {name}"
        return code

    var = symbol_table.get_variable(scope, name)
    offs = offsetof(symbol_table, scope, name)

    ret = CodeSnippet()

    if var.is_arg:
        ret.add_line(gen(offs, True, var.is_16bit))
    elif var.from_global:
        bits = "16" if var.is_16bit else ""
        ret.add_line("PUSH_STACK_START")
        if offs != 0:
            ret.add_line(f"PUSH16 #{offs}")
            ret.add_line("ADD16")
        if load:
            ret.add_line(f"LOAD_GLOBAL{bits}")
        else:
            ret.add_line(f"STORE_GLOBAL{bits}")
    else:
        ret.add_line(gen(offs, False, var.is_16bit))

    return ret


def offsetof(symbol_table: SymbolTable, scope, name: str, search_in_globals=False) -> int:
    offs = 0
    # Check function arguments
    fsig = symbol_table.get_function_signature(scope)
    if fsig and name in fsig.args:
        for k, v in reversed(fsig.args.items()):
            offs += v.stack_size
            if k == name:
                return offs

    # Check global variables, if being in local scope:
    if search_in_globals and scope and symbol_table.get_global_variable(name):
        for k, v in symbol_table.get_all_variables("").items():
            if k == name:
                # v = self._local_variables[""][name]
                return offs
            offs += v.stack_size

    # Check local variables
    if not symbol_table.get_variable(scope, name):
        raise RuntimeError(f"Unknown variable {name}")
    for k, v in symbol_table.get_all_variables(scope).items():
        if v.from_global:
            continue
        if k == name:
            return offs
        offs += v.stack_size


def _gen_address_of_str(symbol_table: SymbolTable, string_constant: str) -> CodeSnippet:
    index = symbol_table.get_index_of_string(string_constant)
    return CodeSnippet(f"PUSH16 @string_{index}")


def _gen_address_of_variable(symbol_table: SymbolTable, scope, var_name) -> CodeSnippet:
    var_def = symbol_table.get_variable(scope, var_name)
    if var_def is None:
        raise RuntimeError(f"Unknown variable {var_name}")
    ret = CodeSnippet()
    if var_def.is_array:
        return gen_load_store_instruction(symbol_table, scope, var_name, True)
    elif var_def.from_global:
        ret.add_line("PUSH_STACK_START")
        offset = offsetof(symbol_table, scope, var_name, True)
        if offset > 0:
            ret.add_line(f"PUSH16 #{offset}")
            ret.add_line("ADD16")
    elif var_def.is_arg:
        ret.add_line("PUSH_REG 2")
        ret.add_line(f"PUSH16 #{offsetof(symbol_table, scope, var_name)}")
        ret.add_line("SUB16")
        ret.add_line("PUSH16 #2")  # saved registers
        ret.add_line("SUB16")
    else:
        ret.add_line("PUSH_REG 2")
        ret.add_line(f"PUSH16 #{offsetof(symbol_table, scope, var_name)}")
        ret.add_line("ADD16")
    return ret
