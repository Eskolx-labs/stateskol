from stateskol.descriptive import mean, median, mode, variance, std, quantile, iqr, histogram_counts
scores = [70, 85, 85, 90, 100]
print("mean", mean(scores))
print("median", median(scores))
print("mode", mode(scores))
print("variance", variance(scores))
print("std", round(std(scores), 2))
print("iqr", iqr(scores))
print("histogram", histogram_counts(scores, [60, 80, 100]))
