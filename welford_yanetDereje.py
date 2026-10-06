def welford(data):
    if not data:
        return 0, 0.0, 0.0, 0.0
        
    count = 0
    mean = 0.0
    M2 = 0.0 
    
    for x in data:
        count += 1
        delta = x - mean
        mean += delta / count
        delta2 = x - mean
        M2 += delta * delta2
        
    if count < 2:
        sample_variance = 0.0
    else:
        sample_variance = M2 / (count - 1)
        
    sample_std_deviation = sample_variance ** 0.5
    
    return count, mean, sample_variance, sample_std_deviation
