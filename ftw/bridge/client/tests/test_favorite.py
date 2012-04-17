from AccessControl import SecurityManagement
from AccessControl.users import SimpleUser
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from StringIO import StringIO
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from ftw.bridge.client.testing import INTEGRATION_TESTING
from ftw.testing import MockTestCase
from mocker import ARGS, KWARGS, ANY
from plone.mocktestcase.dummy import Dummy
from requests.exceptions import ConnectionError
from requests.models import Response
from unittest2 import TestCase
from zope.component import getMultiAdapter


class TestAddWatcherPortletView(TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.mtool = getToolByName(self.portal, 'portal_membership')
        self.folder = self.mtool.getHomeFolder()

    def tearDown(self):
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
        self.assertEquals(link.getRemoteUrl(), 'http://www.google.com/')

    def test_generate_favorite_id(self):
        mock_folder = Dummy(objectIds=lambda: ['favorite-1', 'favorite-2'])
        view = self.portal.restrictedTraverse('@@add-favorite')
        self.assertEqual(view.generate_favorite_id(mock_folder),
                         'favorite-3')


class TestRemoteAddFavoriteAction(MockTestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def setUp(self):
        MockTestCase.setUp(self)

        self.requests = self.mocker.replace('requests')
        # Let the "requests" packaage not do any requests at all while
        # testing. We do this by expecting any request call zero times.
        self.expect(self.requests.request(ARGS, KWARGS)).count(0)

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

    def _create_response(self, status_code=200, raw='response data'):
        response = Response()
        response.status_code = status_code
        response.raw = StringIO(raw)
        return response

    def test_component_is_registered(self):
        self.replay()
        getMultiAdapter((self.page, self.request),
                        name='remote-add-favorite')

    def test_requests_bridge(self):
        favorite_url = '%sfeed-folder/page' % PORTAL_URL_PLACEHOLDER
        bridge_url = 'http://bridge/proxy/dashboard/@@add-favorite'

        self.expect(self.requests.request(
                ANY, bridge_url, headers=ANY,
                params={'title': 'The page',
                        'url': favorite_url})).result(
            self._create_response(raw='OK'))

        self.replay()
        view = getMultiAdapter((self.page, self.request),
                               name='remote-add-favorite')
        view()

    def test_status_message_on_success(self):
        self.expect(self.requests.request(ANY, ANY, KWARGS)).result(
            self._create_response(raw='OK'))

        self.replay()
        view = getMultiAdapter((self.page, self.request),
                               name='remote-add-favorite')
        view()

        messages = IStatusMessage(self.request).show()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message,
                         u'The page was added to your favorites.')
        self.assertEqual(messages[0].type,
                         'info')

    def test_redirects_back(self):
        self.expect(self.requests.request(ANY, ANY, KWARGS)).result(
            self._create_response(raw='OK'))

        self.replay()
        view = getMultiAdapter((self.page, self.request),
                               name='remote-add-favorite')
        view()

        self.assertEqual(self.request.response.headers.get('location'),
                         self.page.absolute_url())

    def test_maintenance_status_message(self):
        self.expect(self.requests.request(ANY, ANY, KWARGS)).result(
            self._create_response(status_code=503, raw='Maintenance'))

        self.replay()
        view = getMultiAdapter((self.page, self.request),
                               name='remote-add-favorite')
        view()

        messages = IStatusMessage(self.request).show()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message,
                         u'The target service is currently in ' + \
                             u'maintenace. Try again later.')
        self.assertEqual(messages[0].type,
                         'error')

    def test_maintenance_redirect(self):
        self.expect(self.requests.request(ANY, ANY, KWARGS)).result(
            self._create_response(status_code=503, raw='Maintenance'))

        self.replay()
        view = getMultiAdapter((self.page, self.request),
                               name='remote-add-favorite')
        view()

        self.assertEqual(self.request.response.headers.get('location'),
                         self.page.absolute_url())

    def test_error_status_message(self):
        self.expect(self.requests.request(ANY, ANY, KWARGS)).result(
            self._create_response(status_code=500, raw='Error'))
        self.replay()

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
        self.expect(self.requests.request(ANY, ANY, KWARGS)).result(
            self._create_response(status_code=500, raw='Error'))

        self.replay()
        view = getMultiAdapter((self.page, self.request),
                               name='remote-add-favorite')
        view()

        self.assertEqual(self.request.response.headers.get('location'),
                         self.page.absolute_url())

    def test_redirects_to_context_when_no_referer_is_found(self):
        if 'HTTP_REFERER' in self.request.environ:
            del self.request.environ['HTTP_REFERER']
        self.expect(self.requests.request(ANY, ANY, KWARGS)).result(
            self._create_response(status_code=500, raw='Error'))

        self.replay()
        view = getMultiAdapter((self.page, self.request),
                               name='remote-add-favorite')
        view()

        self.assertEqual(self.request.response.headers.get('location'),
                         self.page.absolute_url())

    def test_error_status_message_on_requests_exception(self):
        def raise_connection_error(*args, **kwargs):
            raise ConnectionError()

        self.expect(self.requests.request(ANY, ANY, KWARGS)).call(
            raise_connection_error)

        self.replay()

        view = getMultiAdapter((self.page, self.request),
                               name='remote-add-favorite')
        view()

        messages = IStatusMessage(self.request).show()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message,
                         u'The favorite could not be created.')
        self.assertEqual(messages[0].type,
                         'error')
