def add_item(name, price, cart=[]):
    """Add an item to the cart and return the updated cart."""
    cart.append({"name": name, "price": price})
    return cart


def get_cart_total(cart):
    """Return the sum of item prices currently in the cart."""
    return sum(item["price"] for item in cart)


def remove_item(cart, name):
    """Remove the first item matching name from the cart, if present."""
    for item in cart:
        if item["name"] == name:
            cart.remove(item)
            break
    return cart
