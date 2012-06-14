from AccessControl import SecurityManagement
from AccessControl.users import SimpleUser
from Products.statusmessages.interfaces import IStatusMessage
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from ftw.bridge.client.tests.base import RequestAwareTestCase
from plone.uuid.interfaces import IUUID
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
import urllib2


class TestWatchActionView(RequestAwareTestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def setUp(self):
        RequestAwareTestCase.setUp(self)

        user = SimpleUser('john.doe', 'pw', [], [])
        SecurityManagement.newSecurityManager(object(), user)

    def test_component_is_registered(self):
        context = self.stub()
        request = self.stub_request()

        self.replay()

        view = queryMultiAdapter((context, request), name='watch')
        self.assertNotEqual(view, None)

    def test_view_requests_bridge(self):
        context = self.layer['folder']
        request = self.layer['request']
        referer_url = 'http://nohost/plone/some-folder'
        request.environ['HTTP_REFERER'] = referer_url

        feed_path = '@@watcher-feed?uid=%s' % IUUID(context)
        bridge_path = 'http://bridge/proxy/dashboard/@@add-watcher-portlet'

        self._expect_request(url=bridge_path,
                             data={'path': feed_path}).result(
            self._create_response(raw='OK'))

        self.replay()

        view = getMultiAdapter((context, request), name='watch')
        view()
        self.assertEqual(request.response.headers.get('location'),
                         referer_url)

        messages = IStatusMessage(request).show()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message,
                         u'A dashboard portlet was created.')

    def test_maintenance(self):
        context = self.layer['folder']
        request = self.layer['request']
        referer_url = 'http://nohost/plone/some-folder'
        request.environ['HTTP_REFERER'] = referer_url

        self._expect_request().throw(urllib2.HTTPError(
                'url', 503, 'Service Unavailable', None, None))

        self.replay()

        view = getMultiAdapter((context, request), name='watch')
        view()
        self.assertEqual(request.response.headers.get('location'),
                         referer_url)

        messages = IStatusMessage(request).show()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message,
                         u'The target service is currently in ' + \
                             u'maintenace. Try again later.')

    def test_error(self):
        context = self.layer['folder']
        request = self.layer['request']

        self._expect_request().throw(urllib2.HTTPError(
                'url', 500, 'Internal Server Error', None, None))

        self.replay()

        view = getMultiAdapter((context, request), name='watch')
        view()
        self.assertEqual(request.response.headers.get('location'),
                         context.absolute_url())

        messages = IStatusMessage(request).show()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message,
                         u'The dashboard portlet could not be created.')

    def test_error_status_message_on_requests_exception(self):
        context = self.layer['folder']
        request = self.layer['request']

        self._expect_request().throw(
            urllib2.URLError('Connection failed'))

        self.replay()

        view = getMultiAdapter((context, request), name='watch')
        view()
        self.assertEqual(request.response.headers.get('location'),
                         context.absolute_url())

        messages = IStatusMessage(request).show()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message,
                         u'The dashboard portlet could not be created.')

    def test_redirect_to_file_view(self):
        # absolute_url would download the file, therefore we need to redirect
        # to the view - but we do that only for typesUseViewActionInListings
        context = self.layer['file']
        request = self.layer['request']

        self._expect_request().throw(
            urllib2.URLError('Connection failed'))

        self.replay()

        view = getMultiAdapter((context, request), name='watch')
        view()
        self.assertEqual(request.response.headers.get('location'),
                         context.absolute_url() + '/view')
