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


if __name__ == '__main__':
    unittest.main()
