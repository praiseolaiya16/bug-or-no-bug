def summarize_orders(orders):
    """Return a mapping of order id to total price."""
    dict = {}
    for order in orders:
        dict[order["id"]] = order["price"]
    return dict


def total_revenue(orders):
    """Return the sum of all order totals."""
    summary = summarize_orders(orders)
    return sum(summary.values())
