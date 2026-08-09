import hashlib


def calculate_checksum(file_content: bytes) -> str:
    return hashlib.sha256(file_content).hexdigest()