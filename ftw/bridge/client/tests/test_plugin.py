from Products.PluggableAuthService.interfaces import plugins
from copy import copy
from ftw.bridge.client.interfaces import IBridgeConfig
from ftw.bridge.client.plugin import BridgePlugin
from ftw.bridge.client.testing import ZCML_LAYER
from ftw.testing import MockTestCase
from zope.browser.interfaces import IAdding
from zope.component import queryMultiAdapter
from zope.interface.verify import verifyClass


class TestAddBridgePlugin(MockTestCase):

    layer = ZCML_LAYER

    def test_component_is_registered(self):
        adding = self.providing_stub(IAdding)
        request = self.stub_request()

        addview = queryMultiAdapter((adding, request),
                                    name='add-bridge-plugin')
        self.assertNotEqual(addview, None)

    def test_addview_adds_plugin(self):
        context = {}

        adding = self.providing_stub(IAdding)
        request = self.stub_request(stub_response=False)

        request.form = {
            'form.button.Add': 'Add',
            'id': 'the-bridge',
            'title': 'The Bridge',
        }

        adding.context = context
        context['the-bridge'] = self.mock()
        context['the-bridge'].side_effect = lambda obj: isinstance(obj, BridgePlugin)

        adding.absolute_url.return_value = 'http://nohost/acl_users'
        addview = queryMultiAdapter((adding, request),
                                    name='add-bridge-plugin')
        addview()
        request.response.redirect.assert_called_with(
            'http://nohost/acl_users/manage_workspace?'
            'manage_tabs_message=Plugin+added.')


class TestPasPlugin(MockTestCase):

    layer = ZCML_LAYER

    def setUp(self):
        super(TestPasPlugin, self).setUp()
        self.config = self.stub_interface(IBridgeConfig)
        self.config.get_bridge_ips.return_value = ['127.0.0.1', '127.0.0.2']
        self.mock_utility(self.config, IBridgeConfig)

        self.valid_credentials = {'id': 'john.doe',
                                  'login': 'john.doe',
                                  'ip': '127.0.0.1',
                                  'extractor': 'bridge'}

    def test_implements_interfaces(self):
        self.assertTrue(plugins.IExtractionPlugin.implementedBy(BridgePlugin))
        verifyClass(plugins.IExtractionPlugin, BridgePlugin)

        self.assertTrue(plugins.IAuthenticationPlugin.implementedBy(
                BridgePlugin))
        verifyClass(plugins.IAuthenticationPlugin, BridgePlugin)

    def test_extracts_credentials(self):
        request = self.stub_request()
        headers = {'X-BRIDGE-AC': 'john.doe',
                   'X-BRIDGE-ORIGIN': 'client-one'}
        request.get_header.side_effect = lambda key, default: headers.get(key, default)
        request.environ = {'REMOTE_ADDR': '127.0.0.1'}

        plugin = BridgePlugin('bridge')
        self.assertEqual(plugin.extractCredentials(request),
                         {'id': 'john.doe',
                          'login': 'john.doe',
                          'ip': '127.0.0.1'})

    def test_extract_credentials_requires_origin(self):
        request = self.stub_request()
        headers = {'X-BRIDGE-AC': 'john.doe',
                   'X-BRIDGE-ORIGIN': None}
        request.get_header.side_effect = lambda key, default: headers.get(key, default)
        request.environ = {}

        plugin = BridgePlugin('bridge')
        self.assertEqual(
            plugin.extractCredentials(request),
            {})

    def test_extract_credentials_requires_principal(self):
        request = self.stub_request()
        headers = {'X-BRIDGE-AC': None,
                   'X-BRIDGE-ORIGIN': 'client-one'}
        request.get_header.side_effect = lambda key, default: headers.get(key, default)
        request.environ = {}

        plugin = BridgePlugin('bridge')
        self.assertEqual(
            plugin.extractCredentials(request),
            {})

    def test_authenticate_credentials(self):
        plugin = BridgePlugin('bridge')
        plugin.REQUEST = self.create_dummy()

        self.assertEqual(
            plugin.authenticateCredentials(self.valid_credentials),
            ('john.doe', 'john.doe'))

    def test_authenticate_credentials_validates_extractor(self):
        plugin = BridgePlugin('bridge')
        plugin.REQUEST = self.create_dummy()

        creds = copy(self.valid_credentials)
        creds['extractor'] = 'wrong-extractor'

        self.assertEqual(
            plugin.authenticateCredentials(creds),
            None)

    def test_authenticate_credentials_from_bad_ip_fails(self):
        plugin = BridgePlugin('bridge')
        plugin.REQUEST = self.create_dummy()

        creds = copy(self.valid_credentials)
        creds['ip'] = '192.168.1.2'

        self.assertEqual(
            plugin.authenticateCredentials(creds),
            None)

    def test_authenticate_credentials_from_right_ip_succeeds(self):
        plugin = BridgePlugin('bridge')
        plugin.REQUEST = self.create_dummy()

        creds = copy(self.valid_credentials)
        creds['ip'] = '127.0.0.2'

        self.assertEqual(
            plugin.authenticateCredentials(creds),
            ('john.doe', 'john.doe'))

    def test_get_request_ip(self):
        plugin = BridgePlugin('bridge')

        request = self.create_dummy(environ={})
        self.assertEqual(plugin._get_request_ip(request), None)

        request = self.create_dummy(environ={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(plugin._get_request_ip(request), '127.0.0.1')

        request = self.create_dummy(environ={
                'REMOTE_ADDR': '127.0.0.1',
                'HTTP_X_FORWARDED_FOR': '192.168.1.1'})
        self.assertEqual(plugin._get_request_ip(request), '127.0.0.1')

        request = self.create_dummy(environ={
                'REMOTE_ADDR': '127.0.0.1',
                'HTTP_X_FORWARDED_FOR': ' 192.168.1.1 , 10.10.10.10'})
        self.assertEqual(plugin._get_request_ip(request), '127.0.0.1')
