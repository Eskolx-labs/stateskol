"""Reference evidence for Welasma's counting and boundary pack.

This is the only place a third-party library may appear. It compares our
results with numpy on the same data, with an explicit tolerance per row.

Run from the repository root after ``pip install -e ".[reference]"``:

    python examples/reference_check.py
"""

import sys

try:
    import numpy
except ImportError:  # pragma: no cover - exercised only without the extra
    numpy = None

from stateskol.descriptive import count, data_range, frequency_table, max_, min_


def check(name, ours, theirs, tol=0.0):
    """Compare one result and print a single evidence line.

    Every row states its tolerance.  Marks 'ok' or 'FAIL'.
    """
    if isinstance(ours, dict):
        ok = ours == theirs
        diff_str = "exact" if ok else "diff"
    else:
        diff = abs(ours - theirs)
        ok = diff <= tol
        diff_str = "%.2g" % diff
    status = "ok" if ok else "FAIL"
    print(
        "%-28s ours=%-12r theirs=%-12r diff=%-8s tol=%-6s %s"
        % (name, ours, theirs, diff_str, tol, status)
    )
    return ok


def main() -> None:
    if numpy is None:
        print("numpy not installed; install it to run the reference check.")
        raise SystemExit(1)

    ok = True

    data = [4.0, 8.0, 6.0, 5.0, 3.0, 7.0, 3.0]

    ok &= check("count", count(data), int(numpy.size(data)), tol=0)
    ok &= check("min", min_(data), float(numpy.min(data)), tol=0.0)
    ok &= check("max", max_(data), float(numpy.max(data)), tol=0.0)
    ok &= check("range", data_range(data), float(numpy.ptp(data)), tol=0.0)

    values, counts = numpy.unique(data, return_counts=True)
    expected = {float(v): int(c) for v, c in zip(values, counts)}
    ok &= check("frequency_table", frequency_table(data), expected, tol=0)

    data_missing = [1.0, None, float("nan"), 4.0, 4.0, 7.0]
    clean = [v for v in data_missing if v is not None and not (isinstance(v, float) and numpy.isnan(v))]
    ok &= check("count (with missing)", count(data_missing), len(clean), tol=0)
    ok &= check("min (with missing)", min_(data_missing), float(numpy.min(clean)), tol=0.0)
    ok &= check("max (with missing)", max_(data_missing), float(numpy.max(clean)), tol=0.0)

    const = [5.0, 5.0, 5.0, 5.0]
    ok &= check("range (constant)", data_range(const), float(numpy.ptp(const)), tol=0.0)
    ok &= check("frequency_table (constant)", frequency_table(const), {5.0: 4}, tol=0)

    print()
    if ok:
        print("ALL OK")
        raise SystemExit(0)
    else:
        print("FAILURES PRESENT")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
