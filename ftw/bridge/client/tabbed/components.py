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
        client_id = self.config.bridge_remote_client_id
        pagesize = self.config.batching_pagesize
        current_page = self.config.batching_current_page

        results = requester.search_catalog(
            client_id, query, limit=pagesize,
            batching_start=((current_page - 1) * pagesize))

        return self._batch_results(results)

    def _batch_results(self, results):
        total_length = results.get_total_length()
        pagesize = self.config.pagesize
        page = self.config.batching_current_page - 1

        just_left = page * pagesize
        just_right = total_length - len(results) - just_left

        data = ([None] * just_left) + \
            results + \
            ([None] * just_right)
        return data

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

    # Disable custom sort indexes since we have a lazy result.
    custom_sort_indexes = {}

    def custom_sort(self, results, sort_on, sort_reverse):
        return results
