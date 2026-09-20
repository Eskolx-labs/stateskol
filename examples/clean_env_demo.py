"""Clean environment demo. Owner: Yonas keeps it green.

This script must run on a fresh clone after pip install -e ".[dev]".
Week 1 claim: the contract and the basics run end to end. As owner modules
land, Yonas extends this demo one section at a time.
"""

from stateskol._missing import apply_missing
from stateskol._validate import to_float_list
from stateskol.basics import count, data_range, max_, min_


def main() -> None:
    raw = [4, 8, 6, 5, 3, 7, None]
    clean, dropped = apply_missing(to_float_list(raw))
    print("clean:", clean)
    print("dropped:", dropped)
    print("count:", count(raw))
    print("min:", min_(raw))
    print("max:", max_(raw))
    print("range:", data_range(raw))


if __name__ == "__main__":
    main()
