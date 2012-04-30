from ftw.bridge.client.interfaces import IBridgeRequest
from ftw.bridge.client.tabbed import interfaces
from ftw.tabbedview.browser.listing import CatalogListingView
from ftw.table.catalog_source import CatalogTableSource
from zope.component import adapts
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import implements


class BridgeCatalogTableSource(CatalogTableSource):
    """Custom catalog table source quering a remote client.
    """

    adapts(interfaces.IBridgeCatalogTableSourceConfig, Interface)

    def search_results(self, query):
        if self.config.bridge_remote_client_id is None:
            raise ValueError('%s defines no bridge_remote_client_id' % (
                    str(self.config)))

        query = self._remove_path_from_query(query)

        requester = getUtility(IBridgeRequest)
        return requester.search_catalog(
            self.config.bridge_remote_client_id,
            query,
            limit=self.config.batching_pagesize)

    def _remove_path_from_query(self, query):
        if self.config.bridge_remove_path and 'path' in query:
            del query['path']
        return query


class BridgeCatalogListingView(CatalogListingView):
    """A base ``ftw.tabbedview`` view acting as bridge catalog source config.
    """

    implements(interfaces.IBridgeCatalogTableSourceConfig)

    bridge_remote_client_id = None
    bridge_remove_path = True
