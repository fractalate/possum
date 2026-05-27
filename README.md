# Possum

Possum is a tiny, cozy programming language implemented in one Python file.
It is intentionally small: variables, expressions, functions, branches, loops,
input, and output. The flavor comes from the words it uses.

Run a program:

```bash
python3 possum.py hello.possum
```

## A Tiny Program

```possum
scrounge "name? " -> name;
stash clean_name = play single_space(name);

sniff clean_name == "" {
    hiss "the pouch is empty";
} else {
    hiss "hello, ${clean_name}";
}
```

## Language Ideas

Possum programs are built from a few plain instincts:

- `stash name = value;` hides a value away under a name.
- `name = value;` changes an existing stash.
- `hiss value;` prints a value.
- `scrounge "prompt" -> name;` reads one line from standard input.
- `sniff condition { ... } else { ... }` chooses a path.
- `unless condition { ... } else { ... }` chooses the cautious path when something is not true.
- `mosey condition { ... }` repeats while a condition stays true.
- `instinct name(scrap, other) { ... }` defines a function.
- `bring value;` returns from an instinct.
- `play name(arg, other)` calls an instinct or builtin function.
- `dead` is the empty value.

Strings can include `${name}` to show a stashed value.

## Expressions

Possum supports numbers, strings, booleans, and `dead`.

```possum
stash total = 3 * (4 + 2);
stash same = total == 18;
stash message = "total is ${total}";
stash snacks = pouch { "persimmon", "grub", "apple core" };
```

Operators:

```text
not
* / %
+ -
< <= > >=
== !=
and
or
```

Falsey values are `false`, `dead`, `0`, `""`, and empty pouches. Everything else is truthy.

## Builtins

- `play single_space(text)` trims repeated whitespace down to single spaces.
- `play number(text)` converts text to a number.
- `play text(value)` converts a value to display text.
- `play pouch_count(pouch)` returns the number of scraps in a pouch.
- `play pouch_pick(pouch, index)` returns one scrap by zero-based index.
- `play pouch_push(pouch, value)` returns a new pouch with one more scrap.

Pouches must use the `pouch` keyword. There is no bare square-bracket list syntax.

## Example

```possum
instinct three_n(n) {
    sniff n <= 1 {
        bring 1;
    } else {
        sniff n % 2 == 0 {
            bring n / 2;
        } else {
            bring 3 * n + 1;
        }
    }
}

instinct collatz(n) {
    stash count = 1;
    mosey n > 1 {
        n = play three_n(n);
        count = count + 1;
    }
    bring count;
}

stash result = play collatz(1023);
hiss "1023 plays dead after ${result} steps";
```
