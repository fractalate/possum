import re
import sys

class InstinctStdinReadline:
    def __init__(self):
        pass

    def execute_instinct(self, context):
        context.stack.append(sys.stdin.readline().rstrip('\n'))

stdin = {
    "read_line": InstinctStdinReadline(),
}

class ExecutionContext:
    def __init__(self, parent=None):
        self.parent = parent
        self.variables = {}
        self.stack = []

    def set_value(self, variable_name, value):
        self.variables[variable_name] = value

    def get_value(self, variable_name):
        if variable_name in self.variables:
            return self.variables[variable_name]
        elif self.parent:
            return self.parent.get_value(variable_name)
        else:
            raise ValueError(f"undefined variable: {repr(variable_name)}")

    def execute(self, program):
        for command in program:
            command.execute(self)

class ActionInstinct:
    def __init__(self, instinct_name, arguments, program):
        self.instinct_name = instinct_name
        self.arg_name = arguments
        self.program = program

    def execute(self, context):
        context.set_value(self.instinct_name, self)

    def execute_instinct(self, context, *args):
        context = ExecutionContext(parent=context)
        for argument, arg in zip(self.arg_name, args):
            context.set_value(argument, arg)
        return context.execute(self.program)

class ActionScroungeFor:
    def __init__(self, package):
        self.package = package

    def execute(self, context):
        if self.package == "stdin":
            context.set_value(self.package, stdin)
        else:
            raise ValueError(f"scrounge ineffective for {repr(self.package)}")

class ActionRealize:
    def __init__(self, identifier):
        self.identifier = identifier

    def execute(self, context):
        value = context.stack.pop()
        context.set_value(self.identifier, value)

class ActionReturn:
    def __init__(self, expression):
        self.expression = expression

    def execute(self, context):
        if not context.parent:
            raise ValueError("return outside of instinct")
        value = self.expression.evaluate(context)
        context.parent.stack.append(value)

class ActionPlayPossumUntil:
    def __init__(self, instinct_name, arguments):
        self.instinct_name = instinct_name
        self.arguments = arguments

    def execute(self, context):
        instinct = ExpressionVariable(self.instinct_name).evaluate(context)
        arguments = [arg.evaluate(context) for arg in self.arguments]
        return instinct.execute_instinct(context, *arguments)

class ActionHiss:
    def __init__(self, message):
        self.message = message

    def execute(self, context):
        print(self.message.evaluate(context))

class ExpressionVariable:
    def __init__(self, name):
        self.name = name

    def evaluate(self, context):
        parts = self.name.split('.')
        obj = None
        while parts:
            part, parts = parts[0], parts[1:]
            if obj is None:
                obj = context.get_value(part)
            else:
                obj = obj[part]
        return obj

class ExpressionValue:
    def __init__(self, value):
        self.value = value

    def evaluate(self, context):
        if isinstance(self.value, str):
            def replacer(match):
                var_name = match.group(1)
                return str(context.get_value(var_name))
            return re.sub(r'\${(\w+)}', replacer, self.value)
        return self.value

if len(sys.argv) < 2:
    print("usage: python possum.py <script_file>")
    sys.exit(1)

with open(sys.argv[1]) as fin:
    script = fin.read()

class Lines:
    def __init__(self, lines):
        self.lines = lines
        self.index = 0

    def next(self):
        if self.index < len(self.lines):
            line = self.lines[self.index]
            self.index += 1
            return line
        return None
    
lines = []
for line in script.splitlines():
    line = line.strip()
    if line and not line.startswith("#"):
        lines.append(line)
lines = Lines(lines)

class Parser:
    def __init__(self, lines):
        self.lines = lines

    def parse(self):
        program = []
        while line := self.lines.next():
            if line.startswith("scrounge for "):
                package = line[len("scrounge for "):].strip().rstrip(";")
                program.append(ActionScroungeFor(package))
            elif line.startswith("realize "):
                identifier = line[len("realize "):].strip().rstrip(";")
                program.append(ActionRealize(identifier))
            elif line.startswith("instinct "):
                parts = line[len("instinct "):].strip().split()
                assert parts[-1] == "{", "expected '{' at the end of instinct declaration"
                instinct_name = parts[0]
                arguments = parts[1:-1]
                program.append(ActionInstinct(instinct_name, arguments, self.parse()))
            elif line.startswith("return "):
                expression = line[len("return "):].strip().rstrip(";")
                program.append(ActionReturn(self.parse_expression(expression)))
            elif line.startswith("play possum until "):
                rest = line[len("play possum until "):].strip().rstrip(";")
                parts = rest.split()
                instinct_name = parts[0]
                arguments = [self.parse_expression(arg) for arg in parts[1:]]
                program.append(ActionPlayPossumUntil(instinct_name, arguments))
            elif line.startswith("hiss "):
                message = line[len("hiss "):].strip().rstrip(";")
                program.append(ActionHiss(self.parse_expression(message)))
            elif line == "}":
                break
            else:
                print(f"Unrecognized line: {line}")
        return program

    def parse_expression(self, expression):
        if expression.startswith('"') and expression.endswith('"'):
            return ExpressionValue(expression[1:-1])
        return ExpressionVariable(expression)

parser = Parser(lines)
program = parser.parse()

global_context = ExecutionContext()
global_context.execute(program)
