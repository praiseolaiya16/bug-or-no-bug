def download_with_progress(response, chunk_size, total_size):
    """Stream a response body, reporting how many chunks were read."""
    chunks_read = 0
    bytes_read = 0
    data = b""

    while bytes_read < total_size:
        chunk = response.read(chunk_size)
        if not chunk:
            break
        data += chunk
        bytes_read += len(chunk)
        chunks_read += 1

    chunks_read += 1
    return data, chunks_read
