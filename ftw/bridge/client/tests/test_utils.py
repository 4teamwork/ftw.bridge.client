from Products.CMFCore.utils import getToolByName
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from ftw.bridge.client.utils import get_brain_url
from ftw.bridge.client.utils import get_object_url
from ftw.bridge.client.utils import to_utf8_recursively
from unittest2 import TestCase


class TestUtils(TestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def test_get_object_url(self):
        folder = self.layer['folder']
        self.assertEqual(
            get_object_url(folder),
            '%sfeed-folder' % PORTAL_URL_PLACEHOLDER)

    def test_get_brain_url(self):
        catalog = getToolByName(self.layer['portal'], 'portal_catalog')
        query = {'path': {'query': '/plone/feed-folder/page',
                          'depth': 0}}

        brains = catalog(query)
        self.assertEqual(len(brains), 1)

        self.assertEqual(
            get_brain_url(brains[0]),
            '%sfeed-folder/page' % PORTAL_URL_PLACEHOLDER)


class TestToUtf8Recursively(TestCase):

    def test_converts_strings(self):
        self.assertEquals(str, type(to_utf8_recursively(u'foo')))
        self.assertEquals(str, type(to_utf8_recursively('foo')))

    def test_keeps_integers(self):
        self.assertEquals(2, to_utf8_recursively(2))

    def test_converts_lists_recursively(self):
        self.assertEquals([str, str],
                          map(type, to_utf8_recursively([u'foo', 'bar'])))
        self.assertEquals(['foo', 'bar'],
                          to_utf8_recursively([u'foo', 'bar']))

    def test_converts_dicts_recursively(self):
        input = {u'foo': u'Foo',
                 'bar': 'Bar'}

        self.assertEquals([str, str],
                          map(type, to_utf8_recursively(input).keys()))

        self.assertEquals([str, str],
                          map(type, to_utf8_recursively(input).values()))

        # assertEquals does not make any type comparision.
        # We just test that the value is the same.
        self.assertEquals(input, to_utf8_recursively(input))
