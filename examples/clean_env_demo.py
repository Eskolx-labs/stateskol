"""The data contract, demonstrated with nothing installed but the package.

Run from the repository root, in a clean environment:

    pip install -e . --no-deps
    python examples/clean_env_demo.py

Standard library only. No numpy, no pandas. This is the example the Week 2
bar asks for: a reader with an empty virtualenv should be able to see every
rule fire, and see what each refusal says.
"""

import sys
from decimal import Decimal
from fractions import Fraction

from stateskol import ContractError, UnknownPolicyError, as_numeric, count

DATA = [4, 8, 6, None, 5, float("nan"), 3, 7]


def show_refusal(label, value):
    """Print one rejection, or fail loudly if the contract accepted it."""
    try:
        as_numeric([value])
    except ContractError as err:
        print("  {:<24} refused -> {}".format(label, err))
        return True
    print("  {:<24} ACCEPTED, which breaks the contract".format(label))
    return False


def main():
    ok = True
    print("stateskol data contract, v0.1")
    print("python {}\n".format(sys.version.split()[0]))

    print("1. accepted input")
    print("  as_numeric({})".format(DATA))
    print("   ->", as_numeric(DATA))
    print("  count ->", count(DATA), "of", len(DATA), "values are present\n")

    print("2. rejected input, one row per rule")
    for label, value in (
        ("bool", True),
        ("str", "3"),
        ("bytes", b"3"),
        ("complex", 3 + 2j),
        ("Decimal", Decimal("1.5")),
        ("Fraction", Fraction(1, 2)),
        ("inf", float("inf")),
        ("-inf", float("-inf")),
        ("2**53 + 1", 2**53 + 1),
    ):
        ok &= show_refusal(label, value)
    print()

    print("3. the boundary is about conversion, not size")
    print("  as_numeric([2**53])     ->", as_numeric([2**53]))
    print("  as_numeric([1e300])     ->", as_numeric([1e300]))
    print()

    print("4. missing values are a policy, not an error")
    print('  policy="drop"   ->', as_numeric([3, None, 7, float("nan"), 1]))
    try:
        as_numeric([3, None, 7], policy="strict")
        print("  policy='strict' accepted a missing value, which is wrong")
        ok = False
    except ContractError as err:
        print("  policy='strict' ->", err)
    print()

    print("5. empty and all-missing are findings, not crashes")
    print("  as_numeric([])               ->", as_numeric([]))
    print("  count([])                    ->", count([]))
    print("  count([None, nan])           ->", count([None, float("nan")]))
    print()

    print("6. a generator is consumed once")
    seen = []

    def source():
        for value in [1, 2, 3]:
            seen.append(value)
            yield value

    print("  as_numeric(generator)     ->", as_numeric(source()))
    print("  items the generator produced:", len(seen), "(one pass, not two)")
    print()

    print("7. a bad policy is caught before the data is touched")
    drained = []

    def watched():
        for value in (1, 2, 3):
            drained.append(value)
            yield value

    try:
        as_numeric(watched(), policy="impute")
        print("  an unknown policy was accepted, which is wrong")
        ok = False
    except UnknownPolicyError as err:
        print("  ", err)
    print("  values drained on the way to the error:", len(drained))
    print("  0 means the generator was never touched\n")

    print("ALL OK" if ok else "FAILURES PRESENT")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
