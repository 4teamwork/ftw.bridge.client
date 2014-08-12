from ftw.bridge.client.brain import BrainRepresentation
from ftw.bridge.client.brain import BrainResultSet
from ftw.bridge.client.brain import BrainSerializer
from ftw.bridge.client.interfaces import IBrainRepresentation
from ftw.bridge.client.interfaces import IBrainSerializer
from ftw.bridge.client.testing import INTEGRATION_TESTING
from ftw.builder import Builder
from ftw.builder import create
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase
from zope.component import queryUtility
from zope.interface.verify import verifyClass
import json


class TestBrainSerializer(TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        self.folder = create(Builder('folder').titled('Feed folder'))
        create(Builder('page').titled(u'The page with uml\xe4uts')
               .within(self.folder))

    def test_utility_is_registered(self):
        component = queryUtility(IBrainSerializer)
        self.assertNotEqual(None, component)

    def test_component_implements_interface(self):
        self.assertTrue(IBrainSerializer.implementedBy(
                BrainSerializer))
        verifyClass(IBrainSerializer, BrainSerializer)

    def test_serialize_brains(self):
        catalog = getToolByName(self.portal, 'portal_catalog')
        results = catalog(path='/'.join(self.folder.getPhysicalPath()),
                          sort_on='path')

        self.assertEqual(2, len(results))
        folder, page = results
        self.assertEquals('Folder', folder.portal_type)
        self.assertEquals('Document', page.portal_type)

        serializer = BrainSerializer()
        data = serializer.serialize_brains(results)
        self.assertEqual(list, type(data))
        self.assertEqual(2, len(data))

        folder_data, page_data = data

        self.assertEqual(u'***portal_url***feed-folder',
                         folder_data['_url'])
        self.assertEqual(u'Feed folder', folder_data['Title'])
        self.assertEqual(u'feed-folder', folder_data['id'])

        self.assertEqual(
            u'***portal_url***feed-folder/the-page-with-umlauts',
            page_data['_url'])
        self.assertEqual(u'The page with uml\xe4uts',
                         page_data['Title'])
        self.assertEqual(u'the-page-with-umlauts', page_data['id'])

    def test_serialized_data_is_jsonizable(self):
        catalog = getToolByName(self.portal, 'portal_catalog')
        results = catalog(path='/'.join(self.folder.getPhysicalPath()),
                          sort_on='path')

        self.assertEqual(2, len(results))

        serializer = BrainSerializer()
        data = serializer.serialize_brains(results)

        self.assertEqual(data, json.loads(json.dumps(data)))

    def test_deserializing(self):
        catalog = getToolByName(self.folder, 'portal_catalog')
        brains = catalog(path='/'.join(self.folder.getPhysicalPath()),
                          sort_on='path')

        self.assertEqual(2, len(brains))

        serializer = BrainSerializer()
        data = json.dumps(serializer.serialize_brains(brains))

        results = serializer.deserialize_brains(
            json.loads(data), total_length=13)

        self.assertEqual(BrainResultSet, type(results))
        self.assertEqual(2, len(results))
        self.assertEqual(13, results.get_total_length())
        folder, page = results

        self.assertTrue(IBrainRepresentation.providedBy(folder))
        self.assertTrue(IBrainRepresentation.providedBy(page))

        self.assertEqual('Feed folder', folder.Title)
        self.assertEqual('The page with uml\xc3\xa4uts', page.Title)

        # The url would be replaced by the bridge proxy, but here we
        # deserialize it directly.
        self.assertEqual('***portal_url***feed-folder',
                         folder.getURL())
        self.assertEqual(
            '***portal_url***feed-folder/the-page-with-umlauts',
            page.getURL())

        self.assertEqual('Folder', folder.portal_type)
        self.assertEqual('Document', page.portal_type)


class TestBrainResultSet(TestCase):

    def test_result_set(self):
        data = BrainResultSet(['foo', 'bar'], total_length=15)
        self.assertEqual(data[0], 'foo')
        self.assertEqual(data[1], 'bar')
        self.assertEqual(data.get_total_length(), 15)


class TestBrainRepresentation(TestCase):

    def test_component_implements_interface(self):
        self.assertTrue(IBrainRepresentation.implementedBy(
                BrainRepresentation))
        verifyClass(IBrainRepresentation, BrainRepresentation)

    def test_getURL(self):
        obj = BrainRepresentation({'_url': 'http://plone/foo'})
        self.assertEqual(obj.getURL(), 'http://plone/foo')

    def test_attribute_access(self):
        obj = BrainRepresentation({
                'Title': 'Foo',
                'portal_type': 'Folder'})

        self.assertEqual(obj.Title, 'Foo')
        self.assertEqual(obj.portal_type, 'Folder')

        with self.assertRaises(AttributeError) as cm:
            obj.missing_attr

        self.assertEqual(str(cm.exception), 'missing_attr')
