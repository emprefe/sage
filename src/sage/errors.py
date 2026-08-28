class SageError(Exception):
    """Base error with a stable machine-readable code."""

    def __init__(self, code: str, message: str, details=None):
        super().__init__(message)
        self.code = code
        self.details = details


class ValidationError(SageError):
    pass


class TransportError(SageError):
    pass
