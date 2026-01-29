"""Exception classes for cmbenchmark."""


class CannotParseError(Exception):
    """File is not in this parser's format (e.g., wrong XML root/namespace)."""
    pass
