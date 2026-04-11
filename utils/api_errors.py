class APIError(Exception):
    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class ValidationError(APIError):
    def __init__(self, message, details=None):
        super().__init__(message, status_code=400, details=details)


class UnauthorizedError(APIError):
    def __init__(self, message, details=None):
        super().__init__(message, status_code=401, details=details)


class NotFoundError(APIError):
    def __init__(self, message, details=None):
        super().__init__(message, status_code=404, details=details)


class ConflictError(APIError):
    def __init__(self, message, details=None):
        super().__init__(message, status_code=409, details=details)


class ServiceUnavailableError(APIError):
    def __init__(self, message, details=None):
        super().__init__(message, status_code=503, details=details)
