from Products.CMFCore.utils import getToolByName
from ftw.bridge.client.browser import watcher
from ftw.bridge.client.exceptions import MaintenanceError
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from ftw.bridge.client.portlets.watcher import IWatcherPortlet
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from ftw.bridge.client.tests.base import RequestAwareTestCase
from ftw.bridge.client.utils import json
from plone.portlets.constants import USER_CATEGORY
from plone.portlets.interfaces import IPortletManager
from plone.portlets.utils import hashPortletInfo
from plone.uuid.interfaces import IUUID
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryMultiAdapter


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class TestAjaxLoadPortletDataView(RequestAwareTestCase):

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
        RequestAwareTestCase.setUp(self)

        portal = self.layer['portal']
        request = self.layer['request']

        request.environ['HTTP_X_BRIDGE_ORIGIN'] = 'client-one'
        request.form['path'] = '@@watcher-feed?uid=567891234'

        self.assertEqual(watcher.AddWatcherPortlet(portal, request)(), 'OK')

    def test_view(self):
        portal = self.layer['portal']
        request = self.layer['request']
        folder = self.layer['folder']
        page = folder.get('page')

        request.form['uid'] = IUUID(folder)
        feed_view = getMultiAdapter((portal, request), name='watcher-feed')
        feed_data = feed_view()

        portlet, portlet_hash = self._get_portlet_and_hash()
        url = 'http://bridge/proxy/%s/%s' % (portlet.client_id,
                                             portlet.path)

        self._expect_request(url=url).result(self._create_response(
                status_code=200, raw=feed_data))

        self.replay()
        request.form['hash'] = portlet_hash

        view = queryMultiAdapter((portal, request), name='watcher-load-data')
        self.assertNotEqual(view, None)

        dt_format = '%b %d, %Y'

        expected_feed_data = dict(
            title=u'Feed folder',
            details_url=u'%sfeed-folder/@@watcher-recently-modified' % (
                PORTAL_URL_PLACEHOLDER),
            items=[
                dict(title=u'The page with uml\xe4uts',
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

    def test_maintenance_error(self):
        portal = self.layer['portal']
        request = self.layer['request']
        folder = self.layer['folder']

        request.form['uid'] = IUUID(folder)

        _portlet, portlet_hash = self._get_portlet_and_hash()
        self._expect_request().throw(MaintenanceError())

        self.replay()
        request.form['hash'] = portlet_hash

        view = queryMultiAdapter((portal, request), name='watcher-load-data')
        self.assertNotEqual(view, None)

        self.assertEqual(view(), '"MAINTENANCE"')

    def test_view_does_not_fail_when_no_modified_date_is_passed(self):
        portal = self.layer['portal']
        request = self.layer['request']
        folder = self.layer['folder']

        request.form['uid'] = IUUID(folder)
        feed_view = getMultiAdapter((portal, request), name='watcher-feed')
        feed_data = feed_view()

        # modify feed data
        data = json.loads(feed_data)
        for item in data['items']:
            item['modified'] = ''
        data = json.dumps(data)

        _portlet, portlet_hash = self._get_portlet_and_hash()
        self._expect_request().result(self._create_response(
                status_code=200, raw=data))

        self.replay()
        request.form['hash'] = portlet_hash

        view = queryMultiAdapter((portal, request), name='watcher-load-data')
        self.assertNotEqual(view, None)
        self.assertEqual(type(json.loads(view())), dict)
