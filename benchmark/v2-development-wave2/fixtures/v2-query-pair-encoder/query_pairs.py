from urllib.parse import urlencode


def encode_pairs(pairs: list[tuple[str, str]]) -> str:
    return urlencode(pairs)

