from ftw.bridge.client.interfaces import IBrainRepresentation
from ftw.bridge.client.interfaces import IBridgeRequest
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from ftw.builder import Builder
from ftw.builder import create
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
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

    def test_count_unbatched_length(self):
        query = {'path': '/'.join(self.folder.getPhysicalPath()),
                 'sort_on': 'effective',
                 'sort_order': 'reverse',
                 'sort_limit': 1}

        view = getMultiAdapter((self.portal, self.request),
                               name='bridge-search-catalog')

        self.assertEqual(view._count_unbatched_length(query), 2)

    def test_response_contains_unbatched_length(self):
        self.request.form['query'] = json.dumps({
                'path': '/'.join(self.folder.getPhysicalPath()),
                'sort_on': 'effective',
                'sort_order': 'reverse',
                'sort_limit': 1})
        self.request.form['limit'] = 1

        view = getMultiAdapter((self.portal, self.request),
                               name='bridge-search-catalog')

        raw_data = view()
        data = json.loads(raw_data)
        self.assertEqual(len(data), 1)
        self.assertEqual(
            self.request.RESPONSE.getHeader('X-total_results_length'),
            '2')


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
        self.assertEqual(page.getURL(),
                         'http://nohost/plone/feed-folder/page')

        self.assertEqual(folder.portal_type, 'Folder')
        self.assertEqual(page.portal_type, 'Document')

    def test_batched_results_with_respons_headers(self):
        query = {
            'path': '/'.join(self.folder.getPhysicalPath()),
            'sort_on': 'sortable_title',
            'sort_limit': 1}

        utility = getUtility(IBridgeRequest)
        results = utility.search_catalog('current-client', query)

        self.assertEqual(len(results), 1)
        folder = results[0]

        self.assertTrue(IBrainRepresentation.providedBy(folder))
        self.assertEqual(folder.Title, 'Feed folder')

    def test_reverse_sorting(self):
        setRoles(self.layer['portal'], TEST_USER_ID, ['Manager'])
        foo = create(Builder('folder').titled('Foo'))
        create(Builder('folder').titled('Bar').within(foo))

        query = {'path': '/'.join(foo.getPhysicalPath()),
                 'sort_on': 'sortable_title',
                 'sort_order': 'reverse'}
        utility = getUtility(IBridgeRequest)
        results = utility.search_catalog('current-client', query)
        titles = map(lambda brain: brain.Title, results)

        self.assertEquals(['Foo', 'Bar'], titles)
