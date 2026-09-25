def reverse_last_n(items, n):
    """Return the last n items of a list, in reverse order."""
    if n <= 0 or n > len(items):
        return []

    start = len(items) - 1
    stop = len(items) - n - 1
    return items[start:stop:-1]


def last_n_in_order(items, n):
    """Return the last n items of a list, in their original order."""
    return list(reversed(reverse_last_n(items, n)))
