from AccessControl import SecurityManagement
from AccessControl.users import SimpleUser
from Products.statusmessages.interfaces import IStatusMessage
from StringIO import StringIO
from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from ftw.testing import MockTestCase
from mocker import ANY, ARGS, KWARGS
from plone.uuid.interfaces import IUUID
from requests.exceptions import ConnectionError
from requests.models import Response
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter


class TestWatchActionView(MockTestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def setUp(self):
        MockTestCase.setUp(self)

        self.requests = self.mocker.replace('requests')
        # Let the "requests" packaage not do any requests at all while
        # testing. We do this by expecting any request call zero times.
        self.expect(self.requests.request(ARGS, KWARGS)).count(0)

        user = SimpleUser('john.doe', 'pw', [], [])
        SecurityManagement.newSecurityManager(object(), user)

    def _create_response(self, status_code=200, raw='response data'):
        response = Response()
        response.status_code = status_code
        response.raw = StringIO(raw)
        return response

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

        self.expect(self.requests.request(
                ANY, bridge_path, headers=ANY,
                params={'path': feed_path})).result(
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

        feed_path = '@@watcher-feed?uid=%s' % IUUID(context)
        bridge_path = 'http://bridge/proxy/dashboard/@@add-watcher-portlet'

        self.expect(self.requests.request(
                ANY, bridge_path, headers=ANY,
                params={'path': feed_path})).result(
            self._create_response(status_code=503, raw='Maintenance'))

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

        feed_path = '@@watcher-feed?uid=%s' % IUUID(context)
        bridge_path = 'http://bridge/proxy/dashboard/@@add-watcher-portlet'

        self.expect(self.requests.request(
                ANY, bridge_path, headers=ANY,
                params={'path': feed_path})).result(
            self._create_response(status_code=500, raw='Eror'))

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
        def raise_connection_error(*args, **kwargs):
            raise ConnectionError()
        context = self.layer['folder']
        request = self.layer['request']

        self.expect(self.requests.request(ANY, ANY, KWARGS)).call(
            raise_connection_error)

        self.replay()

        view = getMultiAdapter((context, request), name='watch')
        view()
        self.assertEqual(request.response.headers.get('location'),
                         context.absolute_url())

        messages = IStatusMessage(request).show()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message,
                         u'The dashboard portlet could not be created.')
