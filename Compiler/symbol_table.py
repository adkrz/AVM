from typing import Dict, Optional, List

from symbols import StructDefinition, FunctionSignature, Constant, Variable, Type


class SymbolTable:
    def __init__(self):
        self._local_variables: Dict[
            str, Dict[str, "Variable"]] = {}  # per scope, then name+details, in order of occurrence
        self._constants: Dict[
            str, Dict[str, "Constant"]] = {}  # per scope, then name+details, in order of occurrence
        # empty string = global scope

        self._string_constants = []

        self._function_signatures: Dict[str, FunctionSignature] = {}
        self._struct_definitions: Dict[str, "StructDefinition"] = {}

    def register_variable(self, scope: str, name: str, type_: Type, is_array: bool = False, from_global: bool = False,
                           struct_def: Optional[StructDefinition] = None) -> Variable:
        if scope in self._function_signatures:
            if name in self._function_signatures[scope].args:
                return self._function_signatures[scope].args[name]
        vdef = Variable(name, type_, is_array=is_array, from_global=from_global, struct_def=struct_def)
        if scope not in self._local_variables:
            self._local_variables[scope] = {name: vdef}
        else:
            if name not in self._local_variables[scope]:
                self._local_variables[scope][name] = vdef
        return vdef

    def register_constant(self, scope: str, name: str, type_: Type, value: int) -> Constant:
        cdef = Constant(name, type_, value)
        if scope not in self._constants:
            self._constants[scope] = {name: cdef}
        else:
            if name not in self._constants[scope]:
                self._constants[scope][name] = cdef
        return cdef

    def register_function(self, name, signature: FunctionSignature):
        self._function_signatures[name] = signature

    def register_struct(self, name, signature: StructDefinition):
        self._struct_definitions[name] = signature

    def get_variable(self, scope, name: str) -> Variable:
        # Check function arguments
        if (scope in self._function_signatures and name
                in self._function_signatures[scope].args):
            return self._function_signatures[scope].args[name]

        if scope not in self._local_variables:
            raise RuntimeError(f"Current context is empty: {scope}, unknown variable {name}")

        # Check local variables, this includes global declarations
        if name not in self._local_variables[scope]:
            raise RuntimeError(f"Unknown variable {name}")
        return self._local_variables[scope][name]

    def get_constant(self, scope, name: str) -> Optional[Constant]:
        """ Does not throw on error """
        # Local context
        if scope in self._constants:
            if name in self._constants[scope]:
                return self._constants[scope][name]
        # global context
        if scope != "" and "" in self._constants:
            if name in self._constants[""]:
                return self._constants[""][name]
        return None

    def get_global_variable(self, name: str) -> Optional[Variable]:
        if "" not in self._local_variables or name not in self._local_variables[""]:
            return None
        return self._local_variables[""][name]

    def get_index_of_string(self, string_constant: str):
        """ Register string constant and returns its 1-based index.
         In case of repeating strings, reuses them """
        if string_constant not in self._string_constants:
            self._string_constants.append(string_constant)
            index = len(self._string_constants)
        else:
            index = self._string_constants.index(string_constant) + 1
        return index

    def get_struct_definition(self, name: str) -> Optional[StructDefinition]:
        if name in self._struct_definitions:
            return self._struct_definitions[name]
        return None

    def get_function_signature(self, name) -> Optional[FunctionSignature]:
        if name in self._function_signatures:
            return self._function_signatures[name]
        return None

    def get_all_variables(self, scope) -> Dict[str, "Variable"]:
        """ Use empty string to get global vars """
        if scope not in self._local_variables:
            return {}
        return self._local_variables[scope]

    def get_all_strings(self) -> List[str]:
        return self._string_constants