#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import re
import sys
from typing import Any


KEYWORDS = {
    "and",
    "dead",
    "else",
    "false",
    "hiss",
    "instinct",
    "mosey",
    "not",
    "or",
    "play",
    "bring",
    "scrounge",
    "sniff",
    "stash",
    "true",
}


@dataclass
class Token:
    kind: str
    value: Any
    line: int
    column: int


class PossumError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens = []
        while not self.done:
            char = self.peek()
            if char in " \t\r":
                self.advance()
            elif char == "\n":
                self.advance_line()
            elif char == "#":
                self.skip_comment()
            elif char == '"':
                tokens.append(self.string())
            elif char.isdigit():
                tokens.append(self.number())
            elif char.isalpha() or char == "_":
                tokens.append(self.identifier())
            else:
                tokens.append(self.symbol())
        tokens.append(Token("EOF", "", self.line, self.column))
        return tokens

    @property
    def done(self) -> bool:
        return self.index >= len(self.source)

    def peek(self, offset: int = 0) -> str:
        at = self.index + offset
        if at >= len(self.source):
            return "\0"
        return self.source[at]

    def advance(self) -> str:
        char = self.source[self.index]
        self.index += 1
        self.column += 1
        return char

    def advance_line(self) -> None:
        self.index += 1
        self.line += 1
        self.column = 1

    def skip_comment(self) -> None:
        while not self.done and self.peek() != "\n":
            self.advance()

    def string(self) -> Token:
        start_line, start_column = self.line, self.column
        self.advance()
        value = []
        escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
        while not self.done and self.peek() != '"':
            char = self.advance()
            if char == "\n":
                raise PossumError(f"{start_line}:{start_column}: unterminated string")
            if char == "\\":
                if self.done:
                    raise PossumError(f"{start_line}:{start_column}: unterminated string")
                code = self.advance()
                value.append(escapes.get(code, code))
            else:
                value.append(char)
        if self.done:
            raise PossumError(f"{start_line}:{start_column}: unterminated string")
        self.advance()
        return Token("STRING", "".join(value), start_line, start_column)

    def number(self) -> Token:
        start_line, start_column = self.line, self.column
        while self.peek().isdigit():
            self.advance()
        if self.peek() == "." and self.peek(1).isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()
            value = float(self.source_token(start_line, start_column))
        else:
            value = int(self.source_token(start_line, start_column))
        return Token("NUMBER", value, start_line, start_column)

    def identifier(self) -> Token:
        start_line, start_column = self.line, self.column
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()
        value = self.source_token(start_line, start_column)
        kind = value.upper() if value in KEYWORDS else "IDENT"
        return Token(kind, value, start_line, start_column)

    def symbol(self) -> Token:
        start_line, start_column = self.line, self.column
        two = self.peek() + self.peek(1)
        if two in {"==", "!=", "<=", ">=", "->"}:
            self.advance()
            self.advance()
            return Token(two, two, start_line, start_column)
        char = self.advance()
        if char in "{}(),;+-*/%=<>":
            return Token(char, char, start_line, start_column)
        raise PossumError(f"{start_line}:{start_column}: unexpected character {char!r}")

    def source_token(self, line: int, column: int) -> str:
        lines_before = self.source.splitlines(keepends=True)[: line - 1]
        start = sum(len(part) for part in lines_before) + column - 1
        return self.source[start:self.index]


@dataclass
class Program:
    statements: list[Any]

    def run(self, env: "Environment") -> None:
        try:
            for statement in self.statements:
                statement.run(env)
        except ReturnSignal:
            raise PossumError("bring outside of an instinct")


@dataclass
class Block:
    statements: list[Any]

    def run(self, env: "Environment") -> None:
        for statement in self.statements:
            statement.run(env)


@dataclass
class Stash:
    name: Token
    expression: Any

    def run(self, env: "Environment") -> None:
        env.define(self.name.value, self.expression.eval(env))


@dataclass
class Assign:
    name: Token
    expression: Any

    def run(self, env: "Environment") -> None:
        env.assign(self.name.value, self.expression.eval(env))


@dataclass
class Hiss:
    expression: Any

    def run(self, env: "Environment") -> None:
        print(possum_text(self.expression.eval(env)))


@dataclass
class Scrounge:
    prompt: Any | None
    name: Token

    def run(self, env: "Environment") -> None:
        if self.prompt is not None:
            print(possum_text(self.prompt.eval(env)), end="", flush=True)
        env.define(self.name.value, sys.stdin.readline().rstrip("\n"))


@dataclass
class Sniff:
    condition: Any
    then_block: Block
    else_block: Block | None

    def run(self, env: "Environment") -> None:
        if possum_truthy(self.condition.eval(env)):
            self.then_block.run(Environment(env))
        elif self.else_block is not None:
            self.else_block.run(Environment(env))


@dataclass
class Mosey:
    condition: Any
    body: Block

    def run(self, env: "Environment") -> None:
        while possum_truthy(self.condition.eval(env)):
            self.body.run(Environment(env))


@dataclass
class Bring:
    expression: Any

    def run(self, env: "Environment") -> None:
        raise ReturnSignal(self.expression.eval(env))


@dataclass
class Instinct:
    name: Token
    params: list[Token]
    body: Block

    def run(self, env: "Environment") -> None:
        env.define(self.name.value, Function(self.name.value, self.params, self.body, env))


@dataclass
class ExpressionStatement:
    expression: Any

    def run(self, env: "Environment") -> None:
        self.expression.eval(env)


@dataclass
class Literal:
    value: Any

    def eval(self, env: "Environment") -> Any:
        if isinstance(self.value, str):
            return interpolate(self.value, env)
        return self.value


@dataclass
class Variable:
    name: Token

    def eval(self, env: "Environment") -> Any:
        return env.get(self.name.value)


@dataclass
class Unary:
    operator: Token
    right: Any

    def eval(self, env: "Environment") -> Any:
        value = self.right.eval(env)
        if self.operator.kind == "-":
            return -require_number(value, self.operator)
        if self.operator.kind == "NOT":
            return not possum_truthy(value)
        raise PossumError(f"{self.operator.line}:{self.operator.column}: unknown unary operator")


@dataclass
class Binary:
    left: Any
    operator: Token
    right: Any

    def eval(self, env: "Environment") -> Any:
        if self.operator.kind == "OR":
            left = self.left.eval(env)
            return left if possum_truthy(left) else self.right.eval(env)
        if self.operator.kind == "AND":
            left = self.left.eval(env)
            return self.right.eval(env) if possum_truthy(left) else left

        left = self.left.eval(env)
        right = self.right.eval(env)
        op = self.operator.kind
        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return possum_text(left) + possum_text(right)
            return require_number(left, self.operator) + require_number(right, self.operator)
        if op == "-":
            return require_number(left, self.operator) - require_number(right, self.operator)
        if op == "*":
            return require_number(left, self.operator) * require_number(right, self.operator)
        if op == "/":
            return require_number(left, self.operator) / require_number(right, self.operator)
        if op == "%":
            return require_number(left, self.operator) % require_number(right, self.operator)
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return require_number(left, self.operator) < require_number(right, self.operator)
        if op == "<=":
            return require_number(left, self.operator) <= require_number(right, self.operator)
        if op == ">":
            return require_number(left, self.operator) > require_number(right, self.operator)
        if op == ">=":
            return require_number(left, self.operator) >= require_number(right, self.operator)
        raise PossumError(f"{self.operator.line}:{self.operator.column}: unknown binary operator")


@dataclass
class Call:
    name: Token
    args: list[Any]

    def eval(self, env: "Environment") -> Any:
        callee = env.get(self.name.value)
        values = [arg.eval(env) for arg in self.args]
        if not callable(callee):
            raise PossumError(f"{self.name.line}:{self.name.column}: {self.name.value} is not an instinct")
        return callee(values, self.name)


class Function:
    def __init__(self, name: str, params: list[Token], body: Block, closure: "Environment"):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def __call__(self, args: list[Any], token: Token) -> Any:
        if len(args) != len(self.params):
            raise PossumError(
                f"{token.line}:{token.column}: {self.name} expected {len(self.params)} scraps, got {len(args)}"
            )
        local = Environment(self.closure)
        for param, arg in zip(self.params, args):
            local.define(param.value, arg)
        try:
            self.body.run(local)
        except ReturnSignal as signal:
            return signal.value
        return None


class Builtin:
    def __init__(self, name: str, arity: int, fn):
        self.name = name
        self.arity = arity
        self.fn = fn

    def __call__(self, args: list[Any], token: Token) -> Any:
        if len(args) != self.arity:
            raise PossumError(
                f"{token.line}:{token.column}: {self.name} expected {self.arity} scraps, got {len(args)}"
            )
        try:
            return self.fn(*args)
        except ValueError as error:
            raise PossumError(f"{token.line}:{token.column}: {self.name} failed: {error}") from error


class Environment:
    def __init__(self, parent: "Environment | None" = None):
        self.parent = parent
        self.values: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def assign(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value)
            return
        raise PossumError(f"undefined stash {name!r}")

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise PossumError(f"undefined stash {name!r}")


class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    def parse(self) -> Program:
        statements = []
        while not self.check("EOF"):
            statements.append(self.statement())
        return Program(statements)

    def statement(self):
        if self.match("STASH"):
            name = self.consume("IDENT", "expected stash name")
            self.consume("=", "expected '=' after stash name")
            expression = self.expression()
            self.optional_semicolon()
            return Stash(name, expression)
        if self.check("IDENT") and self.peek_next().kind == "=":
            name = self.advance()
            self.consume("=", "expected '=' after stash name")
            expression = self.expression()
            self.optional_semicolon()
            return Assign(name, expression)
        if self.match("HISS"):
            expression = self.expression()
            self.optional_semicolon()
            return Hiss(expression)
        if self.match("SCROUNGE"):
            prompt = None
            if not self.check("->"):
                prompt = self.expression()
            self.consume("->", "expected '->' in scrounge")
            name = self.consume("IDENT", "expected stash name after '->'")
            self.optional_semicolon()
            return Scrounge(prompt, name)
        if self.match("SNIFF"):
            condition = self.expression()
            then_block = self.block()
            else_block = self.block() if self.match("ELSE") else None
            return Sniff(condition, then_block, else_block)
        if self.match("MOSEY"):
            condition = self.expression()
            return Mosey(condition, self.block())
        if self.match("BRING"):
            expression = self.expression()
            self.optional_semicolon()
            return Bring(expression)
        if self.match("INSTINCT"):
            name = self.consume("IDENT", "expected instinct name")
            self.consume("(", "expected '(' after instinct name")
            params = []
            if not self.check(")"):
                while True:
                    params.append(self.consume("IDENT", "expected scrap name"))
                    if not self.match(","):
                        break
            self.consume(")", "expected ')' after scraps")
            return Instinct(name, params, self.block())
        expression = self.expression()
        self.optional_semicolon()
        return ExpressionStatement(expression)

    def block(self) -> Block:
        self.consume("{", "expected '{'")
        statements = []
        while not self.check("}") and not self.check("EOF"):
            statements.append(self.statement())
        self.consume("}", "expected '}'")
        return Block(statements)

    def expression(self):
        return self.or_expr()

    def or_expr(self):
        expr = self.and_expr()
        while self.match("OR"):
            expr = Binary(expr, self.previous(), self.and_expr())
        return expr

    def and_expr(self):
        expr = self.equality()
        while self.match("AND"):
            expr = Binary(expr, self.previous(), self.equality())
        return expr

    def equality(self):
        expr = self.comparison()
        while self.match("==", "!="):
            expr = Binary(expr, self.previous(), self.comparison())
        return expr

    def comparison(self):
        expr = self.term()
        while self.match("<", "<=", ">", ">="):
            expr = Binary(expr, self.previous(), self.term())
        return expr

    def term(self):
        expr = self.factor()
        while self.match("+", "-"):
            expr = Binary(expr, self.previous(), self.factor())
        return expr

    def factor(self):
        expr = self.unary()
        while self.match("*", "/", "%"):
            expr = Binary(expr, self.previous(), self.unary())
        return expr

    def unary(self):
        if self.match("-", "NOT"):
            return Unary(self.previous(), self.unary())
        return self.primary()

    def primary(self):
        if self.match("NUMBER", "STRING"):
            return Literal(self.previous().value)
        if self.match("TRUE"):
            return Literal(True)
        if self.match("FALSE"):
            return Literal(False)
        if self.match("DEAD"):
            return Literal(None)
        if self.match("IDENT"):
            return Variable(self.previous())
        if self.match("PLAY"):
            name = self.consume("IDENT", "expected instinct name after play")
            self.consume("(", "expected '(' after instinct name")
            args = []
            if not self.check(")"):
                while True:
                    args.append(self.expression())
                    if not self.match(","):
                        break
            self.consume(")", "expected ')' after scraps")
            return Call(name, args)
        if self.match("("):
            expr = self.expression()
            self.consume(")", "expected ')'")
            return expr
        token = self.peek()
        raise PossumError(f"{token.line}:{token.column}: expected expression")

    def match(self, *kinds: str) -> bool:
        if self.check(*kinds):
            self.advance()
            return True
        return False

    def consume(self, kind: str, message: str) -> Token:
        if self.check(kind):
            return self.advance()
        token = self.peek()
        raise PossumError(f"{token.line}:{token.column}: {message}")

    def check(self, *kinds: str) -> bool:
        if self.index >= len(self.tokens):
            return False
        return self.peek().kind in kinds

    def advance(self) -> Token:
        token = self.peek()
        self.index += 1
        return token

    def peek(self) -> Token:
        return self.tokens[self.index]

    def peek_next(self) -> Token:
        if self.index + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.index + 1]

    def previous(self) -> Token:
        return self.tokens[self.index - 1]

    def optional_semicolon(self) -> None:
        self.match(";")


def interpolate(value: str, env: Environment) -> str:
    def replace(match):
        return possum_text(env.get(match.group(1)))

    return re.sub(r"\${([A-Za-z_][A-Za-z0-9_]*)}", replace, value)


def require_number(value: Any, token: Token) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PossumError(f"{token.line}:{token.column}: expected a number")
    return value


def possum_truthy(value: Any) -> bool:
    return value not in (False, None, 0, "")


def possum_text(value: Any) -> str:
    if value is None:
        return "dead"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def root_environment() -> Environment:
    env = Environment()
    env.define("single_space", Builtin("single_space", 1, lambda value: " ".join(possum_text(value).split())))
    env.define("number", Builtin("number", 1, lambda value: float(value) if "." in possum_text(value) else int(value)))
    env.define("text", Builtin("text", 1, possum_text))
    return env


def run(source: str) -> None:
    program = Parser(Lexer(source).tokenize()).parse()
    program.run(root_environment())


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 possum.py <script.possum>", file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as script:
            run(script.read())
    except PossumError as error:
        print(f"possum: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"possum: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
