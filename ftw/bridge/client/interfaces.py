# pylint: disable=E0211, E0213
# E0211: Method has no argument
# E0213: Method should have "self" as first argument

from zope.interface import Interface


class IBridgeConfig(Interface):
    """Utility providing bridge configuration infos. Configurable using
    environment variables:

    ``bridge_url`` -- Full url to the bridge /proxy view.
    ``bridge_ips`` -- A comma seperated string of allowed bridge IPs.
    ``bridge_client_id`` -- The id (string) of this client.
    """

    def get_url():
        """Returns the URL to the proxy view of the bridge, ending with a
        slash (/).
        """

    def get_bridge_ips():
        """Returns a list of allowed IP addresses.
        """

    def get_client_id():
        """Returns the client id of this client.
        """


class IBridgeRequest(Interface):
    """A utility for sending requests to the bridge.
    """

    def __call__(target, path, method='GET', headers=None, **kwargs):
        """Make a request to the client ``target`` client through the
        configured bridge.

        Arguments:
        ``target`` -- Target client id as configured on the bridge.
        ``path`` -- Path and view to request, relative to the site root on
        the remote client.
        ``method`` -- Request method (defaults to GET).
        ``headers`` -- Dict of additional request headers (optional).
        **kwargs -- Additional keyword arguments passed to ``requests``
        package.
        """

    def get_json(*args, **kwargs):
        """Makes a request to a view returning json and converts the
        json to python.

        The arguments are the same as for the __call__ method.
        """
