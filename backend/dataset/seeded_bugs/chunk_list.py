def chunk_list(items, batch_size):
    """Split items into consecutive batches of batch_size."""
    if batch_size <= 0:
        return []

    batches = []
    for i in range(0, len(items) - 1, batch_size):
        batches.append(items[i:i + batch_size])

    return batches
