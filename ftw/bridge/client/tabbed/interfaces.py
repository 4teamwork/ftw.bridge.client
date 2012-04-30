from ftw.table.interfaces import ICatalogTableSourceConfig
from zope import schema


class IBridgeCatalogTableSourceConfig(ICatalogTableSourceConfig):
    """A ``ftw.tabbedview`` / ``ftw.table`` table source config interface
    for creating tabs listing content from another client.
    """

    bridge_remote_client_id = schema.TextLine(
        title=u'Remote client id',
        description=u'The ftw.bridge client id of the remote client where '
        u'the catalog should be queried.')

    bridge_remove_path = schema.Bool(
        title=u'Remove path from query',
        description=u'Unless the path is explicitly defined it is not '
        u'useful to use generated paths, since those path start with the '
        u'site path of the querying client and not the one of the queried '
        u'client. Thus we remove the path filters from the catalog query '
        u'by default.',
        default=True)
