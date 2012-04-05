from Products.CMFCore.utils import getToolByName
from StringIO import StringIO
from ftw.bridge.client.browser import watcher
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from ftw.bridge.client.portlets.watcher import IWatcherPortlet
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from ftw.testing import MockTestCase
from mocker import ANY, ARGS, KWARGS
from plone.portlets.constants import USER_CATEGORY
from plone.portlets.interfaces import IPortletManager
from plone.portlets.utils import hashPortletInfo
from plone.uuid.interfaces import IUUID
from requests.models import Response
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryMultiAdapter

try:
    import json
except ImportError:
    import simplejson as json


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class TestAjaxLoadPortletDataView(MockTestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def _get_portlet_and_hash(self):
        context = self.layer['portal']
        column_manager = getUtility(IPortletManager, name='plone.dashboard1')
        membership_tool = getToolByName(context, 'portal_membership')
        userid = membership_tool.getAuthenticatedMember().getId()
        user_category = column_manager.get(USER_CATEGORY, None)
        assert user_category
        column = user_category.get(userid, None)
        assert column

        for portlet in column.values():
            if IWatcherPortlet.providedBy(portlet):
                info = {'manager': 'plone.dashboard1',
                        'category': USER_CATEGORY,
                        'key': userid,
                        'name': portlet.getId()}
                return portlet, hashPortletInfo(info)

    def setUp(self):
        MockTestCase.setUp(self)

        portal = self.layer['portal']
        request = self.layer['request']

        request.environ['HTTP_X_BRIDGE_ORIGIN'] = 'client-one'
        request.form['path'] = '@@watcher-feed?uid=567891234'

        self.assertEqual(watcher.AddWatcherPortlet(portal, request)(), 'OK')

        self.requests = self.mocker.replace('requests')
        # Let the "requests" packaage not do any requests at all while
        # testing. We do this by expecting any request call zero times.
        self.expect(self.requests.request(ARGS, KWARGS)).count(0)

    def test_view(self):
        portal = self.layer['portal']
        request = self.layer['request']
        folder = self.layer['folder']
        page = folder.get('page')

        request.form['uid'] = IUUID(folder)
        feed_view = getMultiAdapter((portal, request), name='watcher-feed')
        feed_data = feed_view()

        response = Response()
        response.status_code = 200
        response.raw = StringIO(feed_data)

        portlet, portlet_hash = self._get_portlet_and_hash()
        self.expect(self.requests.request(
                ANY,
                'http://bridge/proxy/%s/%s' % (portlet.client_id,
                                               portlet.path),
                headers=ANY)).result(response)

        self.replay()
        request.form['hash'] = portlet_hash

        view = queryMultiAdapter((portal, request), name='watcher-load-data')
        self.assertNotEqual(view, None)

        dt_format = folder.portal_properties.site_properties.localTimeFormat

        expected_feed_data = dict(
            title=u'Feed folder',
            details_url=u'%sfeed-folder/recently_modified_view' % (
                PORTAL_URL_PLACEHOLDER),
            items=[
                dict(title=u'The page',
                     url=u'%sfeed-folder/page' % PORTAL_URL_PLACEHOLDER,
                     modified=page.modified().strftime(dt_format),
                     portal_type=u'Document',
                     cssclass=u''),

                dict(title=u'Feed folder',
                     url=u'%sfeed-folder' % PORTAL_URL_PLACEHOLDER,
                     modified=folder.modified().strftime(dt_format),
                     portal_type=u'Folder',
                     cssclass=u''),
                ])

        self.assertEqual(json.loads(view()), expected_feed_data)
