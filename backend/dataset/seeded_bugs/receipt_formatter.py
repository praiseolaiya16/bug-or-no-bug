def format_receipt(items):
    """Build a human-readable receipt string from a list of items."""
    lines = []
    subtotal = 0
    for item in items:
        subtotal += item["price"]
        lines.append(f"{item['name']}: ${item['price']:.2f}")

    tax = subtotal * 0.08
    lines.append(f"Total: ${subtotal:.2f}")
    return "\n".join(lines)
