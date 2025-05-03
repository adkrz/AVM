import unittest

from tests.helpers import Helpers


class TestArrays(unittest.TestCase, Helpers):
    def test_math_expression(self):
        self.compare_programs("math_expression.prg", "math_expression.asm")

    def test_arrays(self):
        self.compare_programs("typed_arrays.prg", "typed_arrays.asm")

    def test_fibonacci(self):
        self.compare_programs("fibonacci_typed.prg", "fibonacci_typed.asm")
