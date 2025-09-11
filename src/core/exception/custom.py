from src.core.exception.reason import Reason


class BaseException(Exception):

    reason: Reason
    details: dict | None = None

    def __init__(self, reason: Reason, details: dict | None = None):
        self.reason = reason
        self.details = details

    def __str__(self):
        return f"{self.__class__.__name__}: {self.reason}" \
            + (f" {self.details}" if self.details is not None else "")


class UserError(BaseException):
    ...


class ServiceError(BaseException):

    details: dict | str = None

    def __init__(self, reason: Reason, details: dict | str = None):
        super().__init__(reason)
        self.details = details