from Products.CMFCore.utils import getToolByName
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from ftw.bridge.client.utils import get_brain_url
from ftw.bridge.client.utils import get_object_url
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
