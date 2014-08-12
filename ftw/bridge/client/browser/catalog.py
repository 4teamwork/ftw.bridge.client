from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from copy import deepcopy
from ftw.bridge.client.interfaces import IBrainSerializer
from ftw.bridge.client.utils import json
from ftw.bridge.client.utils import to_utf8_recursively
from zope.component import getUtility


class BridgeSearchCatalog(BrowserView):

    def __call__(self):
        query = to_utf8_recursively(json.loads(self.request.get('query')))

        # ftw.solr hack https://github.com/4teamwork/ftw.solr/issues/42
        if query.get('path') == '/' or (
            isinstance(query.get('path'), dict) and query['path'].get('query') == '/'):
            del query['path']

        limit = int(self.request.get('limit'))
        brains = self._query_catalog(query, limit)

        total_length = self._count_unbatched_length(query)
        self.request.RESPONSE.setHeader(
            'X-total_results_length', str(total_length))

        return self._serialize_results(brains)

    def _query_catalog(self, query, limit):
        catalog = getToolByName(self.context, 'portal_catalog')

        if 'batching_start' in query:
            batching_start = int(query['batching_start'])
            del query['batching_start']
        else:
            batching_start = 0

        # ftw.solr may destroy our query
        # https://github.com/4teamwork/ftw.solr/issues/41
        query = deepcopy(query)
        brains = catalog(query)
        batching_stop = batching_start + limit

        return brains[batching_start: batching_stop]

    def _serialize_results(self, results):
        serializer = getUtility(IBrainSerializer)
        return json.dumps(serializer.serialize_brains(results))

    def _count_unbatched_length(self, query):
        query = deepcopy(query)

        for key in ('sort_on', 'sort_order', 'sort_limit', 'batching_start'):
            if key in query:
                del query[key]

        catalog = getToolByName(self.context, 'portal_catalog')

        # ftw.solr may destroy our query
        # https://github.com/4teamwork/ftw.solr/issues/41
        query = deepcopy(query)
        brains = catalog(**query)
        return len(brains)
