import re

flags = re.MULTILINE | re.IGNORECASE
optimizations = [
    (re.compile(r"PUSH 0\nADD\n", flags), ""),
    (re.compile(r"PUSH16 #0\nADD16\n", flags), ""),
    (re.compile(r"PUSH 1\nMUL\n", flags), ""),
    (re.compile(r"PUSH16 #1\nMUL16\n", flags), ""),
    (re.compile(r"PUSH [1-9]\d*\nJF @\w+\n", flags), ""),
    (re.compile(r"PUSH 0\nJT @\w+\n", flags), ""),
    (re.compile(r"PUSH 1\nADD", flags), "INC"),
    (re.compile(r"PUSH16 #1\nADD16", flags), "INC16"),
    (re.compile(r"PUSH 1\nSUB2", flags), "DEC"),
    (re.compile(r"PUSH16 #1\nSUB216", flags), "DEC16"),
    (re.compile(r"PUSH16 #0\nPUSH16 #\d+\nMUL16\nADD16\n", flags), ""),
    (re.compile(r"PUSH #0\nPUSH #\d+\nMUL\nADD\n", flags), ""),
    (re.compile(r"PUSH16 #\d+\nPUSH16 #0\nMUL16\nADD16\n", flags), ""),
    (re.compile(r"PUSH #\d+\nPUSH #0\nMUL\nADD\n", flags), ""),
    (re.compile(r"PUSH 0\nEQ", flags), "ZERO"),
    (re.compile(r"PUSH 0\nNE", flags), "NZERO"),
    (re.compile(r"PUSH16 #0\nEQ16", flags), "ZERO16"),
    (re.compile(r"PUSH_NEXT_SP\nPUSH16 #2\nSUB216", flags), "PUSH_REG 1"),
    #(re.compile(r"POPN 1", flags), "POP"),  # interferes with constant folding
    (re.compile(r"RET\nRET", flags), "RET"),
    (re.compile(r"EXTEND\nPUSH16 #2\nMUL16\nADD16", flags), "MACRO_POP_EXT_X2_ADD16"),
    (re.compile(r"EXTEND\nADD16", flags), "MACRO_ADD8_TO_16"),
    (re.compile(r"AND\nEXTEND", flags), "MACRO_ANDX"),
    (re.compile(r"OR\nEXTEND", flags), "MACRO_ORX"),
    (re.compile(r"EXTEND\nLSH16", flags), "MACRO_LSH16_BY8"),
]

# Constant folding
cfold1 = re.compile(r"PUSH (\d+)\nDEC", flags)
cfold2 = re.compile(r"PUSH (\d+)\nINC", flags)
cfold3 = re.compile(r"PUSH16 #(\d+)\nDEC16", flags)
cfold4 = re.compile(r"PUSH16 #(\d+)\nINC16", flags)
cfold_sum1 = re.compile(r"PUSH (\d+)\nPUSH (\d+)\nADD", flags)
cfold_sum2 = re.compile(r"PUSH16 #(\d+)\nPUSH16 #(\d+)\nADD16", flags)
cfold_mul1 = re.compile(r"PUSH (\d+)\nPUSH (\d+)\nMUL", flags)
cfold_mul2 = re.compile(r"PUSH16 #(\d+)\nPUSH16 #(\d+)\nMUL16", flags)
cfold_sum3 = re.compile(r"POPN (\d+)\nPOPN (\d+)", flags)
cfold_addc1 = re.compile(r"PUSH (\d+)\nADD\n", flags)
cfold_addc2 = re.compile(r"PUSH16 #(\d+)\nADD16\n", flags)
cfold_mulc1 = re.compile(r"PUSH (\d+)\nMUL\n", flags)
cfold_mulc2 = re.compile(r"PUSH16 #(\d+)\nMUL16\n", flags)
cfold_push_addc1 = re.compile(r"PUSH (\d+)\nADDC (\d+)\n", flags)
cfold_push_addc2 = re.compile(r"PUSH16 #(\d+)\nADD16C #(\d+)\n", flags)
cfold_push_mulc1 = re.compile(r"PUSH (\d+)\nMULC (\d+)\n", flags)
cfold_push_mulc2 = re.compile(r"PUSH16 #(\d+)\nMUL16C #(\d+)\n", flags)

# Counters = load + inc/dec + store
counter1 = re.compile(r"LOAD_LOCAL (\d+)\nINC\nSTORE_LOCAL (\d+)", flags)
counter2 = re.compile(r"LOAD_LOCAL (\d+)\nDEC\nSTORE_LOCAL (\d+)", flags)
counter3 = re.compile(r"LOAD_LOCAL16 (\d+)\nINC16\nSTORE_LOCAL16 (\d+)", flags)
counter4 = re.compile(r"LOAD_LOCAL16 (\d+)\nDEC16\nSTORE_LOCAL16 (\d+)", flags)


def remove_comments(code: str) -> str:
    code1 = []
    for ll in code.split("\n"):
        if ";" in ll:
            ll = ll[:ll.index(";")]
        ll = ll.strip()
        if ll:
            code1.append(ll)
    return "\n".join(code1)


def optimize(code: str) -> str:
    code = remove_comments(code)
    while 1:
        nn = 0
        for o in optimizations:
            (code, n) = o[0].subn(o[1], code)
            nn += n

        # constant folding
        cfold = cfold1.search(code)
        if cfold:
            value = int(cfold.group(1)) - 1
            code = code.replace(cfold.group(), f"PUSH {value}")
            nn += 1
        cfold = cfold2.search(code)
        if cfold:
            value = int(cfold.group(1)) + 1
            code = code.replace(cfold.group(), f"PUSH {value}")
            nn += 1
        cfold = cfold3.search(code)
        if cfold:
            value = int(cfold.group(1)) - 1
            code = code.replace(cfold.group(), f"PUSH16 #{value}")
            nn += 1
        cfold = cfold4.search(code)
        if cfold:
            value = int(cfold.group(1)) + 1
            code = code.replace(cfold.group(), f"PUSH16 #{value}")
            nn += 1
        cfold = cfold_sum1.search(code)
        if cfold:
            value = int(cfold.group(1)) + int(cfold.group(2))
            code = code.replace(cfold.group(), f"PUSH {value}")
            nn += 1
        cfold = cfold_sum2.search(code)
        if cfold:
            value = int(cfold.group(1)) + int(cfold.group(2))
            code = code.replace(cfold.group(), f"PUSH16 #{value}")
            nn += 1
        cfold = cfold_mul1.search(code)
        if cfold:
            value = int(cfold.group(1)) * int(cfold.group(2))
            code = code.replace(cfold.group(), f"PUSH {value}")
            nn += 1
        cfold = cfold_mul2.search(code)
        if cfold:
            value = int(cfold.group(1)) * int(cfold.group(2))
            code = code.replace(cfold.group(), f"PUSH16 #{value}")
            nn += 1
        cfold = cfold_sum3.search(code)
        if cfold:
            value = int(cfold.group(1)) + int(cfold.group(2))
            code = code.replace(cfold.group(), f"POPN {value}")
            nn += 1
        cfold = cfold_addc1.search(code)
        if cfold:
            value = int(cfold.group(1))
            code = code.replace(cfold.group(), f"ADDC {value}\n")
            nn += 1
        cfold = cfold_addc2.search(code)
        if cfold:
            value = int(cfold.group(1))
            code = code.replace(cfold.group(), f"ADD16C #{value}\n")
            nn += 1
        cfold = cfold_mulc1.search(code)
        if cfold:
            value = int(cfold.group(1))
            code = code.replace(cfold.group(), f"MULC {value}\n")
            nn += 1
        cfold = cfold_mulc2.search(code)
        if cfold:
            value = int(cfold.group(1))
            code = code.replace(cfold.group(), f"MUL16C #{value}\n")
            nn += 1
        cfold = cfold_push_addc1.search(code)
        if cfold:
            value = int(cfold.group(1)) + int(cfold.group(2))
            code = code.replace(cfold.group(), f"PUSH {value}\n")
            nn += 1
        cfold = cfold_push_addc2.search(code)
        if cfold:
            value = int(cfold.group(1)) + int(cfold.group(2))
            code = code.replace(cfold.group(), f"PUSH16 #{value}\n")
            nn += 1
        cfold = cfold_push_mulc1.search(code)
        if cfold:
            value = int(cfold.group(1)) * int(cfold.group(2))
            code = code.replace(cfold.group(), f"PUSH {value}\n")
            nn += 1
        cfold = cfold_push_mulc2.search(code)
        if cfold:
            value = int(cfold.group(1)) * int(cfold.group(2))
            code = code.replace(cfold.group(), f"PUSH16 #{value}\n")
            nn += 1

        counter = counter1.search(code)
        if counter:
            value1 = int(counter.group(1))
            value2 = int(counter.group(2))
            if value1 == value2:
                code = code.replace(counter.group(), f"MACRO_INC_LOCAL {value1}")
        counter = counter2.search(code)
        if counter:
            value1 = int(counter.group(1))
            value2 = int(counter.group(2))
            if value1 == value2:
                code = code.replace(counter.group(), f"MACRO_DEC_LOCAL {value1}")
        counter = counter3.search(code)
        if counter:
            value1 = int(counter.group(1))
            value2 = int(counter.group(2))
            if value1 == value2:
                code = code.replace(counter.group(), f"MACRO_INC_LOCAL16 {value1}")
        counter = counter4.search(code)
        if counter:
            value1 = int(counter.group(1))
            value2 = int(counter.group(2))
            if value1 == value2:
                code = code.replace(counter.group(), f"MACRO_DEC_LOCAL16 {value1}")

        if nn == 0:
            break
    return code
