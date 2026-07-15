"""Domain errors written for people making a product decision."""


class DataProblem(ValueError):
    """An input or configuration problem that the user can correct."""


def friendly_message(exc: Exception) -> str:
    """Return an actionable message without exposing implementation details."""
    if isinstance(exc, DataProblem):
        return str(exc)
    return (
        "GateSignal could not complete this review. Check the edited tables for blank labels, "
        "non-numeric values, or values outside the ranges shown, then try again."
    )
