"""Errors shared across features."""


class UpstreamError(Exception):
    """A call to another service (data, history) failed or returned an unexpected response."""
