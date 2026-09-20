"""Clean environment demo. Owner: Yonas keeps it green.

Stdlib only. This script must run on a fresh clone with nothing installed
except the package itself: pip install -e . --no-deps, then this file.
As owner blocks land, Yonas extends the demo one section at a time.
"""

from stateskol.descriptive import apply_missing, count, data_range, max_, min_, to_float_list


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
