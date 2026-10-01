"""表达式解析与求值模块（后端核心服务层）。

本模块用**手写递归下降解析器**对用户输入的数学表达式进行求值，
从而避免使用 ``eval`` / ``exec`` 等会执行任意代码的危险方式。

支持的语法
-----------
* 二元运算符：``+ - * /``
* 括号：``( )``
* 一元正负号：``-5``、``3 * -2``、``+8``
* 整数与小数：``12``、``3.14``、``.5``
* 空格与换行

文法（EBNF）::

    expression := term (("+" | "-") term)*
    term       := factor (("*" | "/") factor)*
    factor     := ("+" | "-")* primary
    primary    := NUMBER | "(" expression ")"

输入非法或除零时抛出 :class:`CalculatorError`。
"""

from __future__ import annotations

from typing import List, Tuple


class CalculatorError(Exception):
    """表达式非法或无法求值时抛出。"""


# Token 类型常量。
NUMBER = "NUMBER"
OP = "OP"
LPAREN = "LPAREN"
RPAREN = "RPAREN"

Token = Tuple[str, str]


def tokenize(expression: str) -> List[Token]:
    """把表达式字符串切分成 ``(类型, 值)`` 的 token 列表。

    数字、小数点、运算符、括号分别识别；非法字符抛出 CalculatorError。
    """
    tokens: List[Token] = []
    i = 0
    length = len(expression)
    while i < length:
        ch = expression[i]
        if ch in " \t\n\r":
            i += 1
            continue
        if ch.isdigit() or ch == ".":
            start = i
            dot_seen = False
            while i < length and (expression[i].isdigit() or expression[i] == "."):
                if expression[i] == ".":
                    if dot_seen:
                        raise CalculatorError("Invalid number")
                    dot_seen = True
                i += 1
            tokens.append((NUMBER, expression[start:i]))
            continue
        if ch == "(":
            tokens.append((LPAREN, ch))
            i += 1
            continue
        if ch == ")":
            tokens.append((RPAREN, ch))
            i += 1
            continue
        if ch in "+-*/":
            tokens.append((OP, ch))
            i += 1
            continue
        raise CalculatorError("Invalid character: %r" % ch)
    return tokens


class Parser:
    """基于 token 流的递归下降解析器。"""

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self) -> Token:
        token = self.peek()
        if token is not None:
            self.pos += 1
        return token

    def parse(self) -> float:
        if not self.tokens:
            raise CalculatorError("Empty expression")
        value = self.parse_expression()
        if self.peek() is not None:
            # 还有剩余 token（如多余的右括号），说明表达式不合法。
            raise CalculatorError("Invalid expression")
        return value

    def parse_expression(self) -> float:
        """处理加减（优先级最低）。"""
        value = self.parse_term()
        while (
            self.peek() is not None
            and self.peek()[0] == OP
            and self.peek()[1] in "+-"
        ):
            op = self.advance()[1]
            rhs = self.parse_term()
            if op == "+":
                value += rhs
            else:
                value -= rhs
        return value

    def parse_term(self) -> float:
        """处理乘除（优先级高于加减）。"""
        value = self.parse_factor()
        while (
            self.peek() is not None
            and self.peek()[0] == OP
            and self.peek()[1] in "*/"
        ):
            op = self.advance()[1]
            rhs = self.parse_factor()
            if op == "*":
                value *= rhs
            else:
                if rhs == 0:
                    raise CalculatorError("Division by zero")
                value /= rhs
        return value

    def parse_factor(self) -> float:
        """处理一元正负号。"""
        sign = 1
        while (
            self.peek() is not None
            and self.peek()[0] == OP
            and self.peek()[1] in "+-"
        ):
            op = self.advance()[1]
            if op == "-":
                sign = -sign
        return sign * self.parse_primary()

    def parse_primary(self) -> float:
        token = self.peek()
        if token is None:
            raise CalculatorError("Invalid expression")
        if token[0] == NUMBER:
            self.advance()
            try:
                return float(token[1])
            except ValueError as exc:
                raise CalculatorError("Invalid number") from exc
        if token[0] == LPAREN:
            self.advance()
            value = self.parse_expression()
            if self.peek() is None or self.peek()[0] != RPAREN:
                raise CalculatorError("Missing closing parenthesis")
            self.advance()
            return value
        raise CalculatorError("Invalid expression")


def evaluate(expression: str) -> float:
    """求值表达式并返回数值结果。

    输入非法、除零或结果非有限数时抛出 :class:`CalculatorError`。
    """
    tokens = tokenize(expression)
    parser = Parser(tokens)
    value = parser.parse()
    if value != value:  # NaN
        raise CalculatorError("Invalid result")
    if value in (float("inf"), float("-inf")):
        raise CalculatorError("Result out of range")
    return value


def format_result(value: float) -> str:
    """把数值结果转成适合展示/存储的字符串。

    使用 ``.12g`` 格式：最多 12 位有效数字并去掉末尾多余的 0，
    例如 20.0 -> "20"，10/3 -> "3.33333333333"。
    """
    return format(value, ".12g")


def to_json_number(value: float):
    """返回适合放入 JSON ``result`` 字段的数字。

    整数值返回 ``int``（例如 9、20），小数返回四舍五入到 12 位小数的
    ``float``，以消除浮点误差（例如 0.30000000000000004 -> 0.3）。
    """
    if value.is_integer():
        return int(value)
    return round(value, 12)
