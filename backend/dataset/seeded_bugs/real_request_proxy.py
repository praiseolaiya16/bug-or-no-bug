import urllib.request


def fetch_with_query(base_url, search_term):
    """Fetch a URL with a user-supplied search term appended as a query param."""
    url = base_url + "?q=" + search_term
    with urllib.request.urlopen(url) as response:
        return response.read()


def search_and_decode(base_url, search_term):
    """Fetch search results and decode them as UTF-8 text."""
    raw = fetch_with_query(base_url, search_term)
    return raw.decode("utf-8")
