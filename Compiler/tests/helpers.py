from typing import List, Sequence


class Helpers:

    @staticmethod
    def _cleanup_line(line: str):
        if ";" in line:
            line = line[:line.index(";")]
        return line.strip()

    @staticmethod
    def _cleaned_lines(lines: Sequence[str]):
        for line in lines:
            cleaned = Helpers._cleanup_line(line)
            if cleaned:
                yield cleaned

    def assert_string_list_equal(self, expected: Sequence[str], actual: Sequence[str]):
        """
        Custom assertion, that compares 2 string lists being actually source codes.
        Compares line by line with meaningful error.
        Ignores empty lines, comments starting with ; and trims whitespaces
        1st list is expected, 2nd is current
        """
        for number, (line1, line2) in enumerate(
                zip(self._cleaned_lines(expected), self._cleaned_lines(actual), strict=True)):
            if line1 != line2:
                raise AssertionError(f"Mismatch in line {number + 1}: expected '{line1}', got '{line2}'")

    @staticmethod
    def read_file_to_lines(filename: str) -> List[str]:
        with open(filename, "rt") as f:
            return f.readlines()

    @staticmethod
    def read_file_to_string(filename: str) -> str:
        with open(filename, "rt") as f:
            return f.read()

    @staticmethod
    def split_lines(data: Sequence[str]):
        for s in data:
            for ss in s.split("\n"):
                yield ss

    def compare_programs(self, input_file, output_file):
        from recursive_descent_parser import Parser

        program = self.read_file_to_string(input_file)
        parser = Parser(program)
        parser.do_parse()
        output = list(self.split_lines(parser.get_code()))
        expected_output = self.read_file_to_lines(output_file)
        self.assert_string_list_equal(expected_output, output)
