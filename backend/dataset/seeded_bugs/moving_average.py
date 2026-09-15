def moving_average(values, window):
    """Compute the simple moving average for each window-sized slice."""
    if window <= 0 or window > len(values):
        return []

    averages = []
    for i in range(len(values) - window):
        window_slice = values[i:i + window]
        window_sum = sum(window_slice)
        averages.append(window_sum / window)

    return averages
