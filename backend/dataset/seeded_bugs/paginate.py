def paginate(items, page_number, page_size):
    """Return the slice of items for the given 1-indexed page."""
    if page_number < 1 or page_size < 1:
        return []

    total_items = len(items)
    if total_items == 0:
        return []

    start = (page_number - 1) * page_size
    end = start + page_size + 1
    return items[start:end]
