from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from ftw.bridge.client.utils import json
from plone.uuid.interfaces import IUUID
from unittest2 import TestCase
from zope.component import queryMultiAdapter


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class TestWatcherFeedView(TestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def test_component_is_registered(self):
        portal = self.layer['portal']
        request = self.layer['request']

        self.assertNotEquals(
            queryMultiAdapter((portal, request), name='watcher-feed'),
            None)

    def test_feed(self):
        portal = self.layer['portal']
        folder = self.layer['folder']
        page = folder.get('page')
        uid = IUUID(folder)

        request = self.layer['request']
        request.form['uid'] = uid

        view = queryMultiAdapter((portal, request), name='watcher-feed')
        result = view()
        self.assertEqual(type(result), str)

        data = json.loads(result)
        self.assertEqual(data, dict(
                title=u'Feed folder',
                details_url=u'%sfeed-folder/@@watcher-recently-modified' % (
                    PORTAL_URL_PLACEHOLDER),
                items=[
                    dict(title=u'The page with uml\xe4uts',
                         url=u'%sfeed-folder/page' % PORTAL_URL_PLACEHOLDER,
                         modified=page.modified().strftime(DATETIME_FORMAT),
                         portal_type=u'Document',
                         cssclass=u''),

                    dict(title=u'Feed folder',
                         url=u'%sfeed-folder' % PORTAL_URL_PLACEHOLDER,
                         modified=folder.modified().strftime(
                            DATETIME_FORMAT),
                         portal_type=u'Folder',
                         cssclass=u''),
                    ]))
