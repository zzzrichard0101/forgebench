import unicodedata


def canonical_key(value):
    return unicodedata.normalize("NFKC", value).casefold()


def is_available(existing, candidate):
    candidate_key = canonical_key(candidate)
    return all(canonical_key(value) != candidate_key for value in existing)
