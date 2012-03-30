from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from plone.uuid.interfaces import IUUID
from unittest2 import TestCase
from zope.component import queryMultiAdapter

try:
    import json
except ImportError:
    import simplejson as json


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
                items=[
                    dict(title=u'The page',
                         url=u'http://nohost/plone/feed-folder/page',
                         modified=page.modified().strftime(DATETIME_FORMAT),
                         portal_type=u'Document',
                         cssclass=u''),

                    dict(title=u'Feed folder',
                         url=u'http://nohost/plone/feed-folder',
                         modified=folder.modified().strftime(
                            DATETIME_FORMAT),
                         portal_type=u'Folder',
                         cssclass=u''),
                    ]))
