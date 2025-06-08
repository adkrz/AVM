from codegen_helpers import CodeSnippet


def peephole_optimize(snippet: CodeSnippet):
    def line_equal(j, val):
        if j < len(snippet.codes):
            return snippet.codes[j] == val
        return False

    changes = 1
    while changes > 0:
        changes = 0
        for i, line in enumerate(snippet.codes):
            if line == "PUSH 1" and line_equal(i + 1, "ADD"):
                snippet.codes[i] = "INC"
                del snippet.codes[i + 1]
                changes += 1
                break
            if line == "PUSH 1" and line_equal(i + 1, "SUB"):
                snippet.codes[i] = "DEC"
                del snippet.codes[i + 1]
                changes += 1
                break
            if line == "PUSH16 #1" and line_equal(i + 1, "SUB16"):
                snippet.codes[i] = "DEC16"
                del snippet.codes[i + 1]
                changes += 1
                break
            if line == "PUSH16 #1" and line_equal(i + 1, "ADD16"):
                snippet.codes[i] = "INC16"
                del snippet.codes[i + 1]
                changes += 1
                break
            if line == "PUSH16 #1" and line_equal(i + 1, "SUB1616"):
                snippet.codes[i] = "DEC16"
                del snippet.codes[i + 1]
                changes += 1
                break
            if line == "AND" and line_equal(i + 1, "EXTEND"):
                snippet.codes[i] = "MACRO_ANDX"
                del snippet.codes[i + 1]
                changes += 1
                break
            if line == "OR" and line_equal(i + 1, "EXTEND"):
                snippet.codes[i] = "MACRO_ORX"
                del snippet.codes[i + 1]
                changes += 1
                break
            if line == "EXTEND" and line_equal(i + 1, "ADD16"):
                snippet.codes[i] = "MACRO_ADD8_TO_16"
                del snippet.codes[i + 1]
                changes += 1
                break
            if line == "EXTEND" and line_equal(i + 1, "LSH16"):
                snippet.codes[i] = "MACRO_LSH16_BY8"
                del snippet.codes[i + 1]
                changes += 1
                break
            if line == "EXTEND" and line_equal(i + 1, "MACRO_X216") and line_equal(i + 2, "ADD16") and line_equal(i + 3, "LOAD_GLOBAL16"):
                snippet.codes[i] = "MACRO_POP_EXT_X2_ADD16_LG16"
                del snippet.codes[i + 3]
                del snippet.codes[i + 2]
                del snippet.codes[i + 1]
                changes += 1
                break
            if line == "EXTEND" and line_equal(i + 1, "MACRO_X216") and line_equal(i + 2, "ADD16"):
                snippet.codes[i] = "MACRO_POP_EXT_X2_ADD16"
                del snippet.codes[i + 2]
                del snippet.codes[i + 1]
                changes += 1
                break
