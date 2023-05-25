class OverleadOdmError(Exception):
    """OverleadOdmError."""


class ModelNotCreatedError(OverleadOdmError):
    """ModelNotCreatedError."""


class ModelInvalidIndexError(OverleadOdmError):
    """ModelInvalidIndexError."""


class ModelClientError(OverleadOdmError):
    """ModelClientError."""


class ModelDatabaseNameError(OverleadOdmError):
    """ModelDatabaseNameError."""


class ModelCollectionNameError(OverleadOdmError):
    """ModelCollectionNameError."""
