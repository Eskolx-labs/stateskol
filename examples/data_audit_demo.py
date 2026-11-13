
"""Data audit demo. Needs nothing installed except the stateskol package.
 
Run:  python examples/data_audit_demo.py
"""
from stateskol.descriptive import as_numeric, audit, data_range, maximum, minimum
from stateskol.errors import EmptyDataError, StateskolError
 
NAN = float("nan")
 
 
def show(title):
    print(f"\n--- {title} ---")
 
 
show("1. Clean data with two missing values (dropped and recorded)")
data = [4, 1, None, 9, NAN, 6]
a = audit(data)
print("values used :", as_numeric(data))
print("min/max/range:", minimum(data), maximum(data), data_range(data))
print("missing at  :", a.dropped_positions)
print(a.summary)
 
show("2. Strict policy: a missing value is an error, not a silent drop")
try:
    as_numeric(data, policy="strict")
except StateskolError as e:
    print(type(e).__name__ + ":", e)
 
show("3. Rejected input: each refusal names its reason")
for bad in ([1, True], [1, "3"], [1, float("inf")], [2**53 + 1]):
    try:
        as_numeric(bad)
    except StateskolError as e:
        print(f"{bad!r:22} -> {type(e).__name__}: {e}")
 
show("4. Empty and all-missing input")
print("empty audit :", audit([]).summary)
try:
    minimum([None, NAN])
except EmptyDataError as e:
    print("EmptyDataError:", e)
 
show("5. A generator is read exactly once")
gen = (x for x in [1, None, 3])
print(audit(gen).summary)
print("left in generator:", list(gen))
 
