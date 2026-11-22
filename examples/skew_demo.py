"""The Sunday demonstration: an outlier moves the mean, not the median."""
from stateskol.descriptive import mean, median, iqr, stdev
from stateskol.errors import UnsupportedRuleError
from stateskol.descriptive import quantile

base = [1, 2, 2, 3, 4, 4, 5, 6, 7]
with_outlier = base + [48]

print(f"{'':14}{'mean':>8}{'median':>8}{'iqr':>8}{'stdev':>8}")
for label, d in (("nine values", base), ("plus 48", with_outlier)):
    print(f"{label:14}{mean(d):8.2f}{median(d):8.2f}{iqr(d):8.2f}{stdev(d):8.2f}")

print()
print("One value moved the mean a lot and the median not at all.")
print("Which summary would lie about this data, and to whom?")

print()
try:
    quantile(base, 0.25, method="type6")
except UnsupportedRuleError as e:
    print("Refused on purpose:", e)