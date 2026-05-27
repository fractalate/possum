# Possum Language Reference

Possum is a minimal block language. Statements may end with `;`; blocks use
curly braces. Lines beginning with `#` are comments.

## Values

Possum has numbers, strings, booleans, and `dead`.

```possum
stash age = 4;
stash snack = "apple";
stash awake = true;
stash missing = dead;
```

Strings interpolate simple stash names with `${name}`.

## Statements

```possum
stash name = expression;
name = expression;
hiss expression;
scrounge "prompt" -> name;
sniff condition { ... } else { ... }
mosey condition { ... }
instinct name(scrap, other) { ... }
bring expression;
```

`scrounge` may omit the prompt:

```possum
scrounge -> line;
```

## Calls

Function calls use `play`:

```possum
stash tidied = play single_space(raw);
stash answer = play collatz(27);
```

An `instinct` without an explicit `bring` returns `dead`.

## Builtins

```possum
play single_space(value)
play number(value)
play text(value)
```

## Truth

`false`, `dead`, `0`, and `""` are falsey. All other values are truthy.

## Operator Order

From tightest to loosest:

```text
not
* / %
+ -
< <= > >=
== !=
and
or
```
