import secrets
import string


PASSWORD_LENGTH = 6


def generate_password(
    length: int = PASSWORD_LENGTH
) -> str:

    characters = (
        string.ascii_letters
        + string.digits
    )

    return "".join(
        secrets.choice(characters)
        for _ in range(length)
    )