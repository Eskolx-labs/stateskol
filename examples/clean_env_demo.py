"""Clean-environment demo for Welasma's counting and boundary pack.

Standard library only. Run from the repository root after
``pip install -e . --no-deps``:

    python examples/clean_env_demo.py
"""

from stateskol.descriptive import (
    BOUNDARY_CASES,
    count,
    data_range,
    frequency_table,
    max_,
    min_,
)


def main() -> None:
    raw = [4, 8, 6, 5, 3, 7, None, float("nan")]
    print("raw:", raw)
    print("count:", count(raw))
    print("min:", min_(raw))
    print("max:", max_(raw))
    print("range:", data_range(raw))
    print("frequency_table:", frequency_table(raw))
    print()
    print("Canonical boundary cases:")
    for case in BOUNDARY_CASES:
        print("-", case.name, ":", case.description)


if __name__ == "__main__":
    main()
