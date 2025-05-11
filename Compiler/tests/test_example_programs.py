import unittest

from helpers import Helpers


class TestArrays(unittest.TestCase, Helpers):
    def test_math_expression(self):
        self.compare_programs("math_expression.prg", "math_expression.asm")

    def test_arrays(self):
        self.compare_programs("typed_arrays.prg", "typed_arrays.asm")

    def test_fibonacci(self):
        self.compare_programs("fibonacci_typed.prg", "fibonacci_typed.asm")

    def test_mult_table(self):
        self.compare_programs("multiplication_table.prg", "multiplication_table.asm")

    def test_globals(self):
        self.compare_programs("globals.prg", "globals.asm")

    def test_simple_structs(self):
        self.compare_programs("simple_structs.prg", "simple_structs.asm")

    def test_function_structs_global(self):
        self.compare_programs("function_structs_global.prg", "function_structs_global.asm")

    def test_function_structs_arg(self):
        self.compare_programs("function_structs_arg.prg", "function_structs_arg.asm")

    def test_simple_pointers(self):
        self.compare_programs("simple_pointers.prg", "simple_pointers.asm")

    def test_char_ops(self):
        self.compare_programs("char_ops.prg", "char_ops.asm")

    def test_array_index_types(self):
        self.compare_programs("array_index_types.prg", "array_index_types.asm")

    def test_cond16bit(self):
        self.compare_programs("cond_16bit.prg", "cond_16bit.asm")

    def test_bf_interpreter(self):
        self.compare_programs("bf_interpreter.prg", "bf_interpreter.asm")

    def test_bf_interpreter_direct_pointers(self):
        self.compare_programs("bf_interpreter_2.prg", "bf_interpreter_2.asm")

    def test_downcast(self):
        self.compare_programs("test_downcast.prg", "test_downcast.asm")

    def test_forward_declare(self):
        self.compare_programs("forward_declare_func.prg", "forward_declare_func.asm")


if __name__ == '__main__':
    unittest.main()
