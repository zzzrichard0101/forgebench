from pathlib import PurePosixPath


def safe_members(names):
    accepted = []
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            continue
        accepted.append(name)
    return accepted
