from Products.CMFCore.utils import getToolByName
from ftw.bridge.client.brain import BrainRepresentation
from ftw.bridge.client.brain import BrainResultSet
from ftw.bridge.client.brain import BrainSerializer
from ftw.bridge.client.interfaces import IBrainRepresentation
from ftw.bridge.client.interfaces import IBrainSerializer
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from unittest2 import TestCase
from zope.component import queryUtility
from zope.interface.verify import verifyClass
import json


class TestBrainSerializer(TestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def setUp(self):
        self.folder = self.layer['folder']

    def test_utility_is_registered(self):
        component = queryUtility(IBrainSerializer)
        self.assertNotEqual(component, None)

    def test_component_implements_interface(self):
        self.assertTrue(IBrainSerializer.implementedBy(
                BrainSerializer))
        verifyClass(IBrainSerializer, BrainSerializer)

    def test_serialize_brains(self):
        catalog = getToolByName(self.folder, 'portal_catalog')
        results = catalog(path='/'.join(self.folder.getPhysicalPath()),
                          sort_on='path')

        self.assertEqual(len(results), 2)
        folder, page = results
        self.assertEquals(folder.portal_type, 'Folder')
        self.assertEquals(page.portal_type, 'Document')

        serializer = BrainSerializer()
        data = serializer.serialize_brains(results)
        self.assertEqual(type(data), list)
        self.assertEqual(len(data), 2)

        folder_data, page_data = data

        self.assertEqual(folder_data['_url'], u'***portal_url***feed-folder')
        self.assertEqual(folder_data['Title'], u'Feed folder')
        self.assertEqual(folder_data['id'], u'feed-folder')

        self.assertEqual(page_data['_url'],
                         u'***portal_url***feed-folder/page')
        self.assertEqual(page_data['Title'], u'The page with uml\xe4uts')
        self.assertEqual(page_data['id'], u'page')

    def test_serialized_data_is_jsonizable(self):
        catalog = getToolByName(self.folder, 'portal_catalog')
        results = catalog(path='/'.join(self.folder.getPhysicalPath()),
                          sort_on='path')

        self.assertEqual(len(results), 2)

        serializer = BrainSerializer()
        data = serializer.serialize_brains(results)

        self.assertEqual(json.loads(json.dumps(data)), data)

    def test_deserializing(self):
        catalog = getToolByName(self.folder, 'portal_catalog')
        brains = catalog(path='/'.join(self.folder.getPhysicalPath()),
                          sort_on='path')

        self.assertEqual(len(brains), 2)

        serializer = BrainSerializer()
        data = json.dumps(serializer.serialize_brains(brains))

        results = serializer.deserialize_brains(
            json.loads(data), total_length=13)

        self.assertEqual(type(results), BrainResultSet)
        self.assertEqual(len(results), 2)
        self.assertEqual(results.get_total_length(), 13)
        folder, page = results

        self.assertTrue(IBrainRepresentation.providedBy(folder))
        self.assertTrue(IBrainRepresentation.providedBy(page))

        self.assertEqual(folder.Title, 'Feed folder')
        self.assertEqual(page.Title, 'The page with uml\xc3\xa4uts')

        # The url would be replaced by the bridge proxy, but here we
        # deserialize it directly.
        self.assertEqual(folder.getURL(), '***portal_url***feed-folder')
        self.assertEqual(page.getURL(), '***portal_url***feed-folder/page')

        self.assertEqual(folder.portal_type, 'Folder')
        self.assertEqual(page.portal_type, 'Document')


class TestBrainResultSet(TestCase):

    def test_result_set(self):
        data = BrainResultSet(['foo', 'bar'], total_length=15)
        self.assertEqual(data[0], 'foo')
        self.assertEqual(data[1], 'bar')
        self.assertEqual(data.get_total_length(), 15)


class TestBrainRepresentation(TestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def setUp(self):
        self.context = self.layer['folder']

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
