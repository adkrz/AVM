from codegen_helpers import CodeSnippet


def peephole_optimize(snippet: CodeSnippet):
    def line_equal(j, val):
        if j < len(snippet.codes):
            return snippet.codes[j] == val
        return False

    def line_starts_with(j, val):
        if j < len(snippet.codes):
            return snippet.codes[j].startswith(val)
        return False

    changes = 1
    while changes > 0:
        changes = 0
        for i, line in enumerate(snippet.codes):
            if line == "AND" and line_equal(i + 1, "EXTEND"):
                snippet.codes[i] = "MACRO_ANDX"
                snippet.remove_line(i + 1)
                changes += 1
                break
            if line == "OR" and line_equal(i + 1, "EXTEND"):
                snippet.codes[i] = "MACRO_ORX"
                snippet.remove_line(i + 1)
                changes += 1
                break
            if line == "EXTEND" and line_equal(i + 1, "ADD16"):
                snippet.codes[i] = "MACRO_ADD8_TO_16"
                snippet.remove_line(i + 1)
                changes += 1
                break
            if line == "EXTEND" and line_equal(i + 1, "LSH16"):
                snippet.codes[i] = "MACRO_LSH16_BY8"
                snippet.remove_line(i + 1)
                changes += 1
                break
            if line == "EXTEND" and line_equal(i + 1, "MACRO_X216") and line_equal(i + 2, "ADD16") and line_equal(i + 3,
                                                                                                                  "LOAD_GLOBAL16"):
                snippet.codes[i] = "MACRO_POP_EXT_X2_ADD16_LG16"
                snippet.remove_line(i + 3)
                snippet.remove_line(i + 2)
                snippet.remove_line(i + 1)
                changes += 1
                break
            if line == "EXTEND" and line_equal(i + 1, "MACRO_X216") and line_equal(i + 2, "ADD16"):
                snippet.codes[i] = "MACRO_POP_EXT_X2_ADD16"
                snippet.remove_line(i + 2)
                snippet.remove_line(i + 1)
                changes += 1
                break
            if line == "PUSH 2" and line_equal(i + 1, "DIV2"):
                snippet.codes[i] = "MACRO_DIV2"
                snippet.remove_line(i + 1)
                changes += 1
                break
            if line == "PUSH 3" and line_equal(i + 1, "DIV2"):
                snippet.codes[i] = "MACRO_DIV3"
                snippet.remove_line(i + 1)
                changes += 1
                break
            if line == "PUSH 3" and line_equal(i + 1, "MUL"):
                snippet.codes[i] = "MACRO_MUL3"
                snippet.remove_line(i + 1)
                changes += 1
                break

            if line_starts_with(i + 1, "JF "):
                conditions = ["EQ", "NE", "LESS", "LESS_OR_EQ", "GREATER", "GREATER_OR_EQ", "ZERO", "NZERO"]
                if line in conditions:
                    target = snippet.codes[i + 1][3:]
                    idx = conditions.index(line)
                    snippet.codes[i] = f"MACRO_CONDITIONAL_JF {idx} {target}"
                    snippet.remove_line(i + 1)
                    changes += 1
                    break
