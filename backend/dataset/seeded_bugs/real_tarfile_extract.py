import tarfile


def extract_upload(archive_path, destination_dir):
    """Extract an uploaded tar archive into the destination directory."""
    with tarfile.open(archive_path) as archive:
        archive.extractall(destination_dir)


def extract_all_uploads(archive_paths, destination_dir):
    """Extract a batch of uploaded tar archives."""
    for archive_path in archive_paths:
        extract_upload(archive_path, destination_dir)
