"""Reference evidence. Owner: Yonas.

This is the one place numpy and scipy may appear. It proves our numbers
match the trusted libraries on the same datasets, with tolerance stated.
It is evidence, not part of the test suite: it needs numpy installed and
it exits quietly when numpy is missing. Yonas wires each owner block up
as the code lands.
"""

try:
    import numpy
except ImportError:
    numpy = None

from stateskol import descriptive


def check(name, ours, theirs, tol=1e-9):
    diff = abs(ours - theirs)
    mark = "ok" if diff <= tol else "MISMATCH"
    print("%-28s ours=%r theirs=%r diff=%g %s" % (name, ours, theirs, diff, mark))
    return diff <= tol


def main() -> None:
    if numpy is None:
        print("numpy not installed, nothing to compare against. Install numpy to run this evidence.")
        return
    data = [4.0, 8.0, 6.0, 5.0, 3.0, 7.0]
    ok = True
    pending = []
    for name, fn, ref in [
        ("mean", descriptive.mean, float(numpy.mean(data))),
        ("median", descriptive.median, float(numpy.median(data))),
        ("variance", descriptive.variance, float(numpy.var(data, ddof=1))),
        ("std", descriptive.std, float(numpy.std(data, ddof=1))),
        ("min", descriptive.min_, float(numpy.min(data))),
        ("max", descriptive.max_, float(numpy.max(data))),
    ]:
        try:
            ours = fn(data)
        except NotImplementedError:
            pending.append(name)
            print("%-28s pending, owner has not landed it yet" % name)
            continue
        ok &= check(name, ours, ref)
    if not ok:
        raise SystemExit("reference mismatch, see lines marked MISMATCH above")
    print("all landed checks match, %d pending" % len(pending))


if __name__ == "__main__":
    main()
