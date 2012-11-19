# pylint: disable=E0211, E0213
# E0211: Method has no argument
# E0213: Method should have "self" as first argument

from ftw.bridge.client import _
from zope.interface import Interface


PORTAL_URL_PLACEHOLDER = '***portal_url***'


MAINTENANCE_ERROR_MESSAGE = _(
    u'error_msg_maintenance',
    default=u'The target service is currently in maintenace. Try again later.')


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

    def __call__(target, path, headers=None, data=None,
                 silent=False):
        """Make a request to the client ``target`` client through the
        configured bridge.

        Arguments:
        ``target`` -- Target client id as configured on the bridge.
        ``path`` -- Path and view to request, relative to the site root on
        the remote client.
        ``headers`` -- Dict of additional request headers (optional).
        ``data`` -- Dict of data to pass (optional).
        ``silent`` -- Return None on connection error instead of raising
        an exception. The original exception will be added to the error_log.
        """

    def get_json(*args, **kwargs):
        """Makes a request to a view returning json and converts the
        json to python.

        The arguments are the same as for the __call__ method.
        """

    def search_catalog(target, query, limit=50):
        """Search the remote catalog and return a list of
        ``IBrainRepresentation`` objects.

        Arguments:
        ``target`` -- Target client id as configured on the bridge.
        ``query`` -- A jsonizable dict with the catalog query.
        ``limit`` -- Limits the remote result to this number of brains for
        avoiding huge responses. If necessary this can be changed. Defaults
        to 50.
        """


class IBrainSerializer(Interface):
    """A tool for serializing and deserializing a set of brains, so that
    it can be transported to another client.
    The deserialized brains are represented with ``IBrainRepresentation``
    objects providing the original metadata. Those representation objects
    cannot retrieve the object (since the object is on another client).
    """

    def serialize_brains(results):
        """Serialize a list of brains into a jsonizable list.
        """

    def deserialize_brains(data):
        """Deserialize the previously serialized data to
        ``IBrainRepresentation`` objects.
        """


class IBrainRepresentation(Interface):
    """Represents a catalog brain which was transported over the bridge.
    It contains all known remote metadata and some important methods.
    """

    def __init__(data):
        """Creates a brain representation instance by passing in a dict
        created previously be the ``brain_to_data`` method.
        """

    def getURL():
        """Returns the full public url to the object on the remote client.
        """
