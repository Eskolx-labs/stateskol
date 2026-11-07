"""Reference evidence for Welasma's counting and boundary pack.

This is the only place a third-party library may appear. It compares our
results with numpy on the same data, with an explicit tolerance.

Run from the repository root after ``pip install -e ".[reference]"``:

    python examples/reference_check.py
"""

try:
    import numpy
except ImportError:  # pragma: no cover - exercised only without the extra
    numpy = None

from stateskol.descriptive import count, data_range, frequency_table, max_, min_


def check(name, ours, theirs, tol=0.0):
    """Compare one result and print a single evidence line."""
    if isinstance(ours, dict):
        ok = ours == theirs
        diff = 0.0 if ok else float("nan")
    else:
        diff = abs(ours - theirs)
        ok = diff <= tol
    print(
        "%-28s ours=%r theirs=%r diff=%r %s"
        % (name, ours, theirs, diff, "ok" if ok else "MISMATCH")
    )
    return ok


def main() -> None:
    if numpy is None:
        print("numpy not installed; install it to run the reference check.")
        return

    data = [4.0, 8.0, 6.0, 5.0, 3.0, 7.0, 3.0]
    ok = True
    ok &= check("count", count(data), int(numpy.size(data)), 0)
    ok &= check("min", min_(data), float(numpy.min(data)), 0.0)
    ok &= check("max", max_(data), float(numpy.max(data)), 0.0)
    ok &= check("range", data_range(data), float(numpy.ptp(data)), 0.0)

    values, counts = numpy.unique(data, return_counts=True)
    expected = {float(value): int(freq) for value, freq in zip(values, counts)}
    ok &= check("frequency_table", frequency_table(data), expected, 0)

    if not ok:
        raise SystemExit("reference mismatch, see lines marked MISMATCH above")
    print("all reference checks match")


if __name__ == "__main__":
    main()
