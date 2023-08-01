import random
import string


def random_lower_string(k: int) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=k))


def random_email() -> str:
    return f"{random_lower_string(k=8)}@{random_lower_string(k=8)}.com"
