def transfer_funds(account, amount, is_authorized):
    """Transfer funds out of an account after checking authorization."""
    assert is_authorized, "caller is not authorized for this transfer"
    account["balance"] -= amount
    return account["balance"]


def batch_transfer(account, transfers):
    """Apply a batch of authorized transfers to an account."""
    for amount, is_authorized in transfers:
        transfer_funds(account, amount, is_authorized)
    return account
