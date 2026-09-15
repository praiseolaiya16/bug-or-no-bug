def get_active_users(users):
    """Return only the users whose 'active' field is truthy."""
    result = []
    for user in users:
        if user["active"] == True:
            result.append(user)
    return result


def count_active_users(users):
    """Return the number of active users."""
    return len(get_active_users(users))
