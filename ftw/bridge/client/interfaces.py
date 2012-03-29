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


class IBridgeRequestLayer(Interface):
    """A request layer interface for marking requests from a bridge (
    authenticated by the bridge PAS plugin).
    """
