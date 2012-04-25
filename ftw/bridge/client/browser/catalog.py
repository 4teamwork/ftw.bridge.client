from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from ftw.bridge.client.interfaces import IBrainSerializer
from ftw.bridge.client.utils import json
from zope.component import getUtility


class BridgeSearchCatalog(BrowserView):

    def __call__(self):
        brains = self._query_catalog()
        serializer = getUtility(IBrainSerializer)
        return json.dumps(serializer.serialize_brains(brains))

    def _query_catalog(self):
        query = json.loads(self.request.get('query'))
        limit = int(self.request.get('limit'))

        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog(query)

        return brains[:limit]
