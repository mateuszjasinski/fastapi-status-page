class ConfigurationError(Exception):
    """Raised when a check itself is broken rather than merely failing.

    Typically because a check returned a non-``bool`` value. A check may also
    raise it explicitly to signal misconfiguration. A critical check in this
    state takes the overall status to ``configuration_error`` (HTTP 500).
    """
