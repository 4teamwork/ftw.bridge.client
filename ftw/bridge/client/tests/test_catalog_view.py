from ftw.bridge.client.interfaces import IBrainRepresentation
from ftw.bridge.client.interfaces import IBridgeRequest
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from unittest2 import TestCase
from zope.component import getMultiAdapter
from zope.component import getUtility
import json


class TestBridgeSearchCatalogView(TestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def setUp(self):
        self.portal = self.layer['portal']
        self.folder = self.layer['folder']
        self.request = self.layer['request']

    def test_component_registered(self):
        view = self.portal.restrictedTraverse('@@bridge-search-catalog')
        self.assertNotEqual(view, None)

    def test_view_returns_json(self):
        self.request.form['query'] = json.dumps({
                'path': '/'.join(self.folder.getPhysicalPath())})

        self.request.form['limit'] = 50

        view = getMultiAdapter((self.portal, self.request),
                               name='bridge-search-catalog')

        raw_data = view()
        data = json.loads(raw_data)

        self.assertEqual(len(data), 2)

        folder_data, page_data = data

        self.assertEqual(folder_data['_url'], u'***portal_url***feed-folder')
        self.assertEqual(folder_data['Title'], u'Feed folder')
        self.assertEqual(folder_data['id'], u'feed-folder')

        self.assertEqual(page_data['_url'],
                         u'***portal_url***feed-folder/page')
        self.assertEqual(page_data['Title'], u'The page with uml\xe4uts')
        self.assertEqual(page_data['id'], u'page')


class TestCatalogRequest(TestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def setUp(self):
        self.folder = self.layer['folder']

    def test_full_stack_catalog_query_by_traversing(self):
        query = {
            'path': '/'.join(self.folder.getPhysicalPath())}

        utility = getUtility(IBridgeRequest)
        results = utility.search_catalog('current-client', query)

        self.assertEqual(len(results), 2)
        folder, page = results

        self.assertTrue(IBrainRepresentation.providedBy(folder))
        self.assertTrue(IBrainRepresentation.providedBy(page))

        self.assertEqual(folder.Title, 'Feed folder')
        self.assertEqual(page.Title, 'The page with uml\xc3\xa4uts')

        self.assertEqual(folder.getURL(), 'http://nohost/plone/feed-folder')
        self.assertEqual(page.getURL(), 'http://nohost/plone/feed-folder/page')

        self.assertEqual(folder.portal_type, 'Folder')
        self.assertEqual(page.portal_type, 'Document')
