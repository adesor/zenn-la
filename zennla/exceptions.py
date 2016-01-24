"""
Custom exceptions for Zenn-La
"""
import json
from zennla import http


class APIException(Exception):
    """
    Base class for Zenn-La exceptions.
    Subclasses should provide `.status_code` and `.default_detail` properties.
    """
    status_code = http.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '{"detail": "A server error occurred."}'

    def __init__(self, detail=None):
        if detail is not None:
            self.detail = json.dumps(detail)
        else:
            self.detail = json.dumps(self.default_detail)
        self.detail = detail or self.default_detail
        self.detail = json.dumps(
            self.detail if isinstance(
                self.detail, (list, dict)
            ) else {'detail': str(self.detail)}
        )

    def __str__(self):
        return self.detail


class ImproperlyConfigured(APIException):
    """
    Raised when there is a problem with the configuration
    """
    status_code = http.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '{"detail": "Improperly Configured"}'


class NonSerializableException(APIException):
    """
    Raised when a non-serializable object is received by a serializer
    """
    status_code = http.HTTP_400_BAD_REQUEST
    default_detail = '{"detail": "Object is not serializable"}'


class ValidationError(APIException):
    """
    Raised when the request made is not valid
    """
    status_code = http.HTTP_400_BAD_REQUEST
    default_detail = '{"detail": "Invalid request"}'
