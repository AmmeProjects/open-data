

def remove_spaces(s: str | None) -> str | None:
    """Remove all spaces from a string."""
    if s is None:
        return None
    return s.replace(" ", "")
