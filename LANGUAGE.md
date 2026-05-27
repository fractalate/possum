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
stash snacks = pouch { "persimmon", "grub", "apple core" };
stash empty_snacks = pouch {};
```

Strings interpolate simple stash names with `${name}`.

## Statements

```possum
stash name = expression;
name = expression;
hiss expression;
scrounge "prompt" -> name;
sniff condition { ... } else { ... }
unless condition { ... } else { ... }
mosey condition { ... }
instinct name(scrap, other) { ... }
bring expression;
```

`scrounge` may omit the prompt:

```possum
scrounge -> line;
```

`unless` runs its first block when the condition is falsey. If an `else` block
is present, it runs when the condition is truthy.

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
play pouch_count(pouch)
play pouch_pick(pouch, index)
play pouch_push(pouch, value)
```

Pouch literals always require `pouch`; Possum does not have bare square-bracket
list syntax.

## Truth

`false`, `dead`, `0`, `""`, and empty pouches are falsey. All other values are truthy.

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
