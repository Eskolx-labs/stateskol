"""One outlier moves the mean and leaves the median alone.

Runs with nothing installed but the package:
    python examples/skew_demo.py
"""

from stateskol.descriptive import mean, median, mode

sample = [1, 2, 2, 3, 4, 4, 5, 6, 7]
with_outlier = sample + [48]

print("data                      mean    median  mode")
for label, data in (("1 2 2 3 4 4 5 6 7", sample), ("same, plus 48", with_outlier)):
    print("{:<25} {:<7.2f} {:<7.2f} {}".format(label, mean(data), median(data), mode(data)))

print()
print("The mean moved by {:.2f}. The median moved by {:.2f}.".format(
    mean(with_outlier) - mean(sample), median(with_outlier) - median(sample)))
print("The mean answers 'what is the total, shared out'. The median answers 'what is the middle case'.")

assert round(mean(sample), 2) == 3.78 and mean(with_outlier) == 8.2
assert median(sample) == median(with_outlier) == 4.0
