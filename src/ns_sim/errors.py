class NSSimError(Exception):
    """Base error for NS-SIM."""


class ConfigurationError(NSSimError):
    """The experiment contract is malformed or unsupported."""


class NumericalError(NSSimError):
    """The canonical numerical runtime failed a hard run condition."""
