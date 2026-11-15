"""Documentation example for count and minimum. Needs only the package.

Run:  python examples/core_a_demo.py
"""

from stateskol.descriptive import count, minimum

readings = [4, None, 2.5, float("nan"), 7]

print("readings:", readings)
print("count   :", count(readings))      # 3: None and NaN are dropped
print("minimum :", minimum(readings))    # 2.5

print("empty count:", count([]))         # 0, an empty file is a finding

try:
    minimum([])
except ValueError as error:   # it is an EmptyDataError
    print("empty minimum refused:", error)

try:
    minimum([1, True])                   # True is not a measurement
except TypeError as error:
    print("bool refused:", type(error).__name__)