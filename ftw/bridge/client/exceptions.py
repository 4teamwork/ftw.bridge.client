class BridgeConfigurationError(Exception):
    """The bridge was not configured well.
    """


class MaintenanceError(Exception):
    """The request to the remote client failed because the remote client is
    in maintenance mode.
    """
