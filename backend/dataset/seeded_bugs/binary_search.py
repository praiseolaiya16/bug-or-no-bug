def binary_search(sorted_items, target):
    """Return the index of target in sorted_items, or -1 if not found."""
    low = 0
    high = len(sorted_items) - 1

    while low < high:
        mid = (low + high) // 2
        if sorted_items[mid] == target:
            return mid
        elif sorted_items[mid] < target:
            low = mid + 1
        else:
            high = mid - 1

    return -1
