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
        super(TestWatchActionView, self).setUp()

        user = SimpleUser('john.doe', 'pw', [], [])
        SecurityManagement.newSecurityManager(object(), user)

    def test_component_is_registered(self):
        context = self.stub()
        request = self.stub_request()

        view = queryMultiAdapter((context, request), name='watch')
        self.assertNotEqual(view, None)

    def test_view_requests_bridge(self):
        context = self.layer['folder']
        request = self.layer['request']
        referer_url = 'http://nohost/plone/some-folder'
        request.environ['HTTP_REFERER'] = referer_url

        feed_path = '@@watcher-feed?uid=%s' % IUUID(context)
        bridge_path = 'http://bridge/proxy/dashboard/@@add-watcher-portlet'

        response = self._create_response(raw='OK')

        with self.patch(response):
            view = getMultiAdapter((context, request), name='watch')
            view()
            self.assertEqual(request.response.headers.get('location'),
                             referer_url)

            self.assertUrl(bridge_path)
            self.assertData({'path': feed_path})

        messages = IStatusMessage(request).show()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, u'A dashboard portlet was created.')

    def test_maintenance(self):
        context = self.layer['folder']
        request = self.layer['request']
        referer_url = 'http://nohost/plone/some-folder'
        request.environ['HTTP_REFERER'] = referer_url

        error = urllib2.HTTPError('url', 503, 'Service Unavailable', None, None)
        with self.patch(error=error):
            view = getMultiAdapter((context, request), name='watch')
            view()
            self.assertEqual(request.response.headers.get('location'),
                             referer_url)

        messages = IStatusMessage(request).show()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message,
                         u'The target service is currently in maintenace. '
                         'Try again later.')

    def test_error(self):
        context = self.layer['folder']
        request = self.layer['request']

        error = urllib2.HTTPError('url', 500, 'Internal Server Error', None, None)
        with self.patch(error=error):
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

        error = urllib2.URLError('Connection failed')
        with self.patch(error=error):
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

        error = urllib2.URLError('Connection failed')
        with self.patch(error=error):
            view = getMultiAdapter((context, request), name='watch')
            view()
            self.assertEqual(request.response.headers.get('location'),
                             context.absolute_url() + '/view')
