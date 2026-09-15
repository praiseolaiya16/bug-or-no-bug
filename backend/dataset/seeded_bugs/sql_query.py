import sqlite3


def get_user_by_username(db_path, username):
    """Look up a user record by username."""
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    query = "SELECT id, username, email FROM users WHERE username = '%s'" % username
    cursor.execute(query)
    result = cursor.fetchone()

    connection.close()
    return result
