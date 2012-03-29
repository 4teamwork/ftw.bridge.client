from AccessControl import SecurityManagement
from AccessControl.users import SimpleUser
from StringIO import StringIO
from ftw.bridge.client.exceptions import MaintenanceError
from ftw.bridge.client.interfaces import IBridgeRequest
from ftw.bridge.client.testing import BRIDGE_CONFIG_LAYER
from ftw.testing import MockTestCase
from mocker import ANY, ARGS, KWARGS
from requests.models import Response
from zope.component import queryUtility, getUtility
from zope.interface.verify import verifyClass


class TestBridgeRequestUtility(MockTestCase):

    layer = BRIDGE_CONFIG_LAYER

    def setUp(self):
        MockTestCase.setUp(self)

        self.requests = self.mocker.replace('requests')
        # Let the "requests" packaage not do any requests at all while
        # testing. We do this by expecting any request call zero times.
        self.expect(self.requests.request(ARGS, KWARGS)).count(0)

        user = SimpleUser('john.doe', 'pw', [], [])
        SecurityManagement.newSecurityManager(object(), user)

    def tearDown(self):
        SecurityManagement.noSecurityManager()

    def _create_response(self, status_code=200, raw='response data'):
        response = Response()
        response.status_code = status_code
        response.raw = StringIO(raw)
        return response

    def test_component_is_registered(self):
        self.replay()
        utility = queryUtility(IBridgeRequest)
        self.assertNotEqual(utility, None)

    def test_implements_interface(self):
        self.replay()
        utility = getUtility(IBridgeRequest)
        klass = type(utility)

        self.assertTrue(IBridgeRequest.implementedBy(klass))
        verifyClass(IBridgeRequest, klass)

    def test_request_path(self):
        response = self._create_response()
        self.expect(self.requests.request(
                ANY,
                'http://bridge/proxy/target-client/path/to/@@something',
                headers=ANY)).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        self.assertEqual(
            utility('target-client', 'path/to/@@something'),
            response)

    def test_request_path_with_leading_slash(self):
        response = self._create_response()
        self.expect(self.requests.request(
                ANY,
                'http://bridge/proxy/target-client/@@something',
                headers=ANY)).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        self.assertEqual(
            utility('target-client', '/@@something'),
            response)

    def test_request_method_default(self):
        response = self._create_response()
        self.expect(self.requests.request(
                'get',
                ANY,
                headers=ANY)).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)


        self.assertEqual(
            utility('target-client', '@@something'),
            response)

    def test_request_method_POST(self):
        response = self._create_response()
        self.expect(self.requests.request(
                'post',
                ANY,
                headers=ANY)).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        self.assertEqual(
            utility('target-client', '@@something', method='POST'),
            response)

    def test_request_default_headers(self):
        response = self._create_response()
        self.expect(self.requests.request(
                ANY,
                ANY,
                headers={'X-BRIDGE-ORIGIN': 'current-client',
                         'X-BRIDGE-AC': 'john.doe'})).result(
            response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        self.assertEqual(
            utility('target-client', '@@something2'),
            response)

    def test_request_custom_headers(self):
        response = self._create_response()
        self.expect(self.requests.request(
                ANY,
                ANY,
                headers={'X-BRIDGE-ORIGIN': 'current-client',
                         'X-BRIDGE-AC': 'john.doe',
                         'X-CUSTOM-HEADER': 'some data'})).result(
            response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        headers = {'X-CUSTOM-HEADER': 'some data'}
        self.assertEqual(len(headers), 1)
        self.assertEqual(
            utility('target-client', '@@something',
                    headers={'X-CUSTOM-HEADER': 'some data'}),
            response)
        self.assertEqual(len(headers), 1)

    def test_additional_arguments(self):
        response = self._create_response()
        self.expect(self.requests.request(
                ANY,
                ANY,
                headers=ANY,
                cookies={'aCookie': 'peanut butter cookie'})).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)
        self.assertEqual(
            utility('target-client', '@@something',
                    cookies={'aCookie': 'peanut butter cookie'}),
            response)

    def test_maintenance_response_raises_exception(self):
        response = self._create_response(status_code='503',
                                         raw='Service Unavailable')
        self.expect(self.requests.request(
                ANY,
                ANY,
                headers=ANY)).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        with self.assertRaises(MaintenanceError):
            utility('target-client', '@@something')

    def test_get_json(self):
        response = self._create_response(raw='[{"foo": "bar"}]')
        self.expect(self.requests.request(
                ANY,
                'http://bridge/proxy/target-client/@@json-view',
                headers=ANY)).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        self.assertEqual(
            utility.get_json('target-client', '@@json-view'),
            [{'foo': 'bar'}])
