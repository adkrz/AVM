from enum import Enum


class Symbol(Enum):
    Nothing = -1
    Plus = ord('+')
    Minus = ord('-')
    Mult = ord('*')
    Divide = ord('/')
    Semicolon = ord(';')
    Becomes = ord('=')
    LParen = ord('(')
    RParen = ord(')')
    LBracket = ord('[')
    RBracket = ord(']')
    LCurly = ord('{')
    RCurly = ord('}')
    Number = 256
    Identifier = 259
    EOF = 260
    Equals = 261
    NotEqual = 262
    Gt = 263
    Ge = 264
    Lt = 265
    Le = 266
    # Negate = 267
    If = 268
    Then = 269
    Else = 270
    And = 271
    Or = 272
    Begin = 273
    End = 274
    While = 275
    Do = 276
    Continue = 277
    Break = 278
    Function = 279
    Return = 280
    Call = 281
    Ampersand = 282
    Comma = 283
    Print = 284
    PrintNewLine = 285
    # QuotationMark = 286
    String = 287
    Modulo = 288
    Global = 289
    Byte = 290
    Addr = 291
    Struct = 292
    Dot = 293
    Char = 294
    PrintChar = 295
    Debugger = 296
    Halt = 297
    Const = 298
    Hash = 299
    PrintStr = 300
    Rsh = 301
    Lsh = 302
    Pipe = ord("|")
    Hat = ord("^")
    Tilde = ord("~")


class Lexer:
    def __init__(self, input_string: str):
        self._input_string = input_string
        self._position = 0
        self._line_number = 1
        self._current_number = 0
        self._current_identifier = ""
        self._current_string = ""

        self._current = Symbol.Nothing

    def backup_state(self) -> list:
        return [self._position, self._line_number, self._current_number, self._current_identifier, self._current_string,
                self._current]

    def restore_state(self, state: list):
        self._position = state[0]
        self._line_number = state[1]
        self._current_number = state[2]
        self._current_identifier = state[3]
        self._current_string = state[4]
        self._current = state[5]

    @property
    def current(self) -> Symbol:
        return self._current

    @property
    def line_number(self):
        return self._line_number

    @property
    def current_identifier(self) -> str:
        return self._current_identifier

    @property
    def current_string(self) -> str:
        return self._current_string

    @property
    def current_number(self):
        return self._current_number

    def _getchar(self) -> str:
        if self._position < len(self._input_string):
            ret = self._input_string[self._position]
            self._position += 1
            return ret
        return ""

    def _rewind(self):
        if self._position > 0:
            self._position -= 1

    def _peek(self) -> str:
        if self._position < len(self._input_string):
            return self._input_string[self._position]
        return ""

    def next_symbol(self):
        buffer = ""
        buffer_mode = 0  # 1: number 2: identifier 3: string
        # previous_mode = current

        while 1:
            t = self._getchar()

            if buffer_mode == 1:
                if t.isdigit() or t == '.':
                    buffer += t
                    continue
                else:
                    self._current_number = int(buffer) if '.' not in buffer else float(buffer)
                    if t != "":
                        self._rewind()
                    return
            elif buffer_mode == 3:
                if t != '"' or (t == '"' and buffer and buffer[-1] == '\\'):
                    buffer += t
                    continue
                else:
                    self._current_string = buffer
                    return
            elif buffer_mode == 4:
                if t != "'" or (t == "'" and buffer and buffer[-1] == '\\'):
                    buffer += t
                    continue
                else:
                    self._current_string = buffer
                    return
            elif buffer_mode == 2:
                if t.isalnum() or t == '_':
                    buffer += t
                    continue
                else:
                    if t != "":
                        self._rewind()

                    buffer_l = buffer.lower()
                    if buffer_l == "if":
                        self._current = Symbol.If
                        return
                    elif buffer_l == "then":
                        self._current = Symbol.Then
                        return
                    elif buffer_l == "else":
                        self._current = Symbol.Else
                        return
                    elif buffer_l == "begin":
                        self._current = Symbol.Begin
                        return
                    elif buffer_l == "end":
                        self._current = Symbol.End
                        return
                    elif buffer_l == "while":
                        self._current = Symbol.While
                        return
                    elif buffer_l == "do":
                        self._current = Symbol.Do
                        return
                    elif buffer_l == "continue":
                        self._current = Symbol.Continue
                        return
                    elif buffer_l == "break":
                        self._current = Symbol.Break
                        return
                    elif buffer_l == "function":
                        self._current = Symbol.Function
                        return
                    elif buffer_l == "const":
                        self._current = Symbol.Const
                        return
                    elif buffer_l == "return":
                        self._current = Symbol.Return
                        return
                    elif buffer_l == "call":
                        self._current = Symbol.Call
                        return
                    elif buffer_l == "print":
                        self._current = Symbol.Print
                        return
                    elif buffer_l == "printnl":
                        self._current = Symbol.PrintNewLine
                        return
                    elif buffer_l == "printch":
                        self._current = Symbol.PrintChar
                        return
                    elif buffer_l == "debugger":
                        self._current = Symbol.Debugger
                        return
                    elif buffer_l == "halt":
                        self._current = Symbol.Halt
                        return
                    elif buffer_l == "global":
                        self._current = Symbol.Global
                        return
                    elif buffer_l == "byte":
                        self._current = Symbol.Byte
                        return
                    elif buffer_l == "addr":
                        self._current = Symbol.Addr
                        return
                    elif buffer_l == "struct":
                        self._current = Symbol.Struct
                        return
                    elif buffer_l == "printstr":
                        self._current = Symbol.PrintStr
                        return

                    self._current_identifier = buffer
                    return

            if not t:
                self._current = Symbol.EOF
                return
            elif t in (' ', '\t', '\r'):
                continue
            elif t == '\n':
                self._line_number += 1
                continue
            elif t == ".":
                self._current = Symbol.Dot
                return
            elif t.isdigit() or t == '.':  # or (t == '-' and peek().isdigit()):
                self._current = Symbol.Number
                buffer += t
                buffer_mode = 1
                continue
            elif t.isalnum():
                self._current = Symbol.Identifier
                buffer += t
                buffer_mode = 2
                continue
            elif t == "\"":
                self._current = Symbol.String
                buffer_mode = 3
                continue
            elif t == "'":
                self._current = Symbol.Char
                buffer_mode = 4
                continue
            elif t == "=":
                if self._peek() == "=":
                    self._current = Symbol.Equals
                    self._getchar()
                else:
                    self._current = Symbol.Becomes
                return
            elif t == "+":
                self._current = Symbol.Plus
                return
            elif t == "-":
                self._current = Symbol.Minus
                return
            elif t == "*":
                self._current = Symbol.Mult
                return
            elif t == "/" and self._peek() != "/":  # divide vs comment
                self._current = Symbol.Divide
                return
            elif t == ";":
                self._current = Symbol.Semicolon
                return
            elif t == "(":
                self._current = Symbol.LParen
                return
            elif t == ")":
                self._current = Symbol.RParen
                return
            elif t == ">":
                if self._peek() == "=":
                    self._current = Symbol.Ge
                    self._getchar()
                elif self._peek() == ">":
                    self._current = Symbol.Rsh
                    self._getchar()
                else:
                    self._current = Symbol.Gt
                return
            elif t == "<":
                if self._peek() == "=":
                    self._current = Symbol.Le
                    self._getchar()
                elif self._peek() == "<":
                    self._current = Symbol.Lsh
                    self._getchar()
                else:
                    self._current = Symbol.Lt
                return
            elif t == "!":
                if self._peek() == "=":
                    self._current = Symbol.NotEqual
                    self._getchar()
                # else:
                #    current = Symbol.Negate
                return
            elif t == "&":
                if self._peek() == "&":
                    self._current = Symbol.And
                    self._getchar()
                else:
                    self._current = Symbol.Ampersand
                return
            elif t == "|":
                if self._peek() == "|":
                    self._current = Symbol.Or
                    self._getchar()
                else:
                    self._current = Symbol.Pipe
                return
            elif t == "/" and self._peek() == "/":
                while self._peek() != '\n' and self._peek() != "":
                    self._getchar()
            elif t == ',':
                self._current = Symbol.Comma
                return
            elif t == '[':
                self._current = Symbol.LBracket
                return
            elif t == ']':
                self._current = Symbol.RBracket
                return
            elif t == '{':
                self._current = Symbol.LCurly
                return
            elif t == '}':
                self._current = Symbol.RCurly
                return
            elif t == '|':
                self._current = Symbol.Pipe
                return
            elif t == '~':
                self._current = Symbol.Tilde
                return
            elif t == '^':
                self._current = Symbol.Hat
                return
            elif t == '%':
                self._current = Symbol.Modulo
                return
            elif t == '#':
                self._current = Symbol.Hash
                return
