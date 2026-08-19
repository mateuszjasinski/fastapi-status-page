from enum import StrEnum


class Status(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    FAIL = "fail"
    CONFIGURATION_ERROR = "configuration_error"


class ResponseFormat(StrEnum):
    JSON = "json"
    HTML = "html"
