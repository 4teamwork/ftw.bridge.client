from AccessControl import SecurityManagement
from AccessControl.users import SimpleUser
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from ftw.bridge.client.testing import INTEGRATION_TESTING
from ftw.bridge.client.tests.base import RequestAwareTestCase
from ftw.testing.testcase import Dummy
from unittest2 import TestCase
from zope.component import getMultiAdapter
import urllib2


class TestAddWatcherPortletView(TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        super(TestAddWatcherPortletView, self).setUp()

        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.mtool = getToolByName(self.portal, 'portal_membership')
        self.folder = self.mtool.getHomeFolder()

    def tearDown(self):
        super(TestAddWatcherPortletView, self).tearDown()

        if 'title' in self.request.form:
            del self.request.form['title']

        if 'url' in self.request.form:
            del self.request.form['url']

        if 'Favorites' in self.folder.objectIds():
            self.folder.manage_delObjects(['Favorites'])

    def test_component_is_registered(self):
        self.portal.restrictedTraverse('@@add-favorite')

    def test_get_favorites_folder(self):
        self.assertNotIn('Favorites', self.folder.objectIds())
        view = self.portal.restrictedTraverse('@@add-favorite')
        folder = view.get_favorites_folder()
        self.assertNotEquals(folder, None)
        self.assertIn('Favorites', self.folder.objectIds())

    def test_adds_link_object(self):
        self.assertNotIn('Favorites', self.folder.objectIds())
        view = self.portal.restrictedTraverse('@@add-favorite')

        self.request.form['title'] = 'Google search'
        self.request.form['url'] = 'http://www.google.com/'

        self.assertEquals(view(), 'OK')
        folder = view.get_favorites_folder()
        self.assertEquals(len(folder.objectValues()), 1)
        link = folder.objectValues()[0]
        self.assertEquals(link.Title(), 'Google search')
        self.assertEquals(link.remoteUrl, 'http://www.google.com/')

    def test_generate_favorite_id(self):
        mock_folder = Dummy(objectIds=lambda: ['favorite-1', 'favorite-2'])
        view = self.portal.restrictedTraverse('@@add-favorite')
        self.assertEqual(view.generate_favorite_id(mock_folder),
                         'favorite-3')


class TestRemoteAddFavoriteAction(RequestAwareTestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def setUp(self):
        super(TestRemoteAddFavoriteAction, self).setUp()

        user = SimpleUser('john.doe', 'pw', [], [])
        SecurityManagement.newSecurityManager(object(), user)

        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.page = self.portal.get('feed-folder').get('page')
        self.referer_url = 'http://nohost/plone/feed-folder/page'
        self.request.environ['HTTP_REFERER'] = self.referer_url

    def tearDown(self):
        IStatusMessage(self.request).show()
        if 'HTTP_REFERER' in self.request.environ:
            del self.request.environ['HTTP_REFERER']
        SecurityManagement.noSecurityManager()

        if 'location' in self.request.response.headers:
            del self.request.response.headers['location']
        super(TestRemoteAddFavoriteAction, self).tearDown()

    def test_component_is_registered(self):
        getMultiAdapter((self.page, self.request),
                        name='remote-add-favorite')

    def test_requests_bridge(self):
        favorite_url = '%sfeed-folder/page' % PORTAL_URL_PLACEHOLDER
        bridge_url = 'http://bridge/proxy/dashboard/@@add-favorite'

        response = self._create_response(raw='OK')
        with self.patch(response):
            view = getMultiAdapter((self.page, self.request),
                                   name='remote-add-favorite')
            view()
            self.assertData({'title': 'The page with uml\xc3\xa4uts',
                             'url': favorite_url})

    def test_status_message_on_success(self):
        response = self._create_response(raw='OK')
        with self.patch(response):
            view = getMultiAdapter((self.page, self.request),
                                   name='remote-add-favorite')
            view()

            messages = IStatusMessage(self.request).show()
            self.assertEqual(len(messages), 1)
            self.assertEqual(
                messages[0].message,
                u'The page with uml\xe4uts was added to your favorites.')
            self.assertEqual(messages[0].type, 'info')

    def test_redirects_back(self):
        response = self._create_response(raw='OK')
        with self.patch(response):
            view = getMultiAdapter((self.page, self.request),
                                   name='remote-add-favorite')
            view()

            self.assertEqual(self.request.response.headers.get('location'),
                             self.page.absolute_url())

    def test_maintenance_status_message(self):
        error = urllib2.HTTPError('url', 503, 'Service Unavailable', None, None)
        with self.patch(error=error):
            view = getMultiAdapter((self.page, self.request),
                                   name='remote-add-favorite')
            view()

            messages = IStatusMessage(self.request).show()
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].message,
                             u'The target service is currently in maintenace. '
                             u'Try again later.')
            self.assertEqual(messages[0].type,
                             'error')

    def test_maintenance_redirect(self):
        error = urllib2.HTTPError('url', 503, 'Service Unavailable', None, None)
        with self.patch(error=error):
            view = getMultiAdapter((self.page, self.request),
                                   name='remote-add-favorite')
            view()

            self.assertEqual(self.request.response.headers.get('location'),
                             self.page.absolute_url())

    def test_error_status_message(self):
        response = self._create_response(raw='Error', status_code=500)
        with self.patch(response):
            view = getMultiAdapter((self.page, self.request),
                                   name='remote-add-favorite')
            view()

            messages = IStatusMessage(self.request).show()
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].message,
                             u'The favorite could not be created.')
            self.assertEqual(messages[0].type,
                             'error')

    def test_error_redirect(self):
        response = self._create_response(raw='Error', status_code=500)
        with self.patch(response):
            view = getMultiAdapter((self.page, self.request),
                                   name='remote-add-favorite')
            view()

            self.assertEqual(self.request.response.headers.get('location'),
                             self.page.absolute_url())

    def test_redirects_to_context_when_no_referer_is_found(self):
        if 'HTTP_REFERER' in self.request.environ:
            del self.request.environ['HTTP_REFERER']

        response = self._create_response(raw='Error', status_code=500)
        with self.patch(response):
            view = getMultiAdapter((self.page, self.request),
                                   name='remote-add-favorite')
            view()

            self.assertEqual(self.request.response.headers.get('location'),
                             self.page.absolute_url())

    def test_error_status_message_on_requests_exception(self):
        error = urllib2.URLError('Connection failed')
        with self.patch(error=error):
            view = getMultiAdapter((self.page, self.request),
                                   name='remote-add-favorite')
            view()

            messages = IStatusMessage(self.request).show()
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].message,
                             u'The favorite could not be created.')
            self.assertEqual(messages[0].type, 'error')

    def test_redirect_to_file_view(self):
        # absolute_url would download the file, therefore we need to redirect
        # to the view - but we do that only for typesUseViewActionInListings
        error = urllib2.URLError('Connection failed')
        with self.patch(error=error):
            if 'HTTP_REFERER' in self.request.environ:
                del self.request.environ['HTTP_REFERER']

            context = self.portal.get('file')
            view = getMultiAdapter((context, self.request),
                                   name='remote-add-favorite')
            view()
            self.assertEqual(self.request.response.headers.get('location'),
                             context.absolute_url() + '/view')

    def test_file_url_has_view_in_favoritte(self):
        # absolute_url would download the file, therefore we need to set the
        # favorite to point to the view - but we do that only for
        # typesUseViewActionInListings.

        favorite_url = '%sfile/view' % PORTAL_URL_PLACEHOLDER
        bridge_url = 'http://bridge/proxy/dashboard/@@add-favorite'

        response = self._create_response(raw='OK')
        with self.patch(response):
            context = self.portal.get('file')
            view = getMultiAdapter((context, self.request),
                                   name='remote-add-favorite')
            view()
            self.assertUrl(bridge_url)
            self.assertData({'title': 'the file', 'url': favorite_url})
