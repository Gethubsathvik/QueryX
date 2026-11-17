"""Errors raised by the charts feature."""


class ChartError(ValueError):
    """The chosen chart cannot be built from this data. The message is shown to the user."""
