from ftw.bridge.client.exceptions import BridgeConfigurationError
from ftw.bridge.client.interfaces import IBridgeConfig
from ftw.bridge.client.testing import ZCML_LAYER
from ftw.testing import MockTestCase
from zope.component import queryUtility, getUtility
from zope.interface.verify import verifyClass
import os


class TestConfig(MockTestCase):

    layer = ZCML_LAYER

    def test_component_is_registered(self):
        config = queryUtility(IBridgeConfig)
        self.assertNotEqual(config, None)

    def test_implement_interface(self):
        config = getUtility(IBridgeConfig)
        klass = type(config)

        self.assertTrue(IBridgeConfig.implementedBy(klass))
        verifyClass(IBridgeConfig, klass)

    def test_get_url(self):
        os.environ['bridge_url'] = 'http://localhost:8000/proxy'
        config = queryUtility(IBridgeConfig)
        self.assertEqual(config.get_url(), 'http://localhost:8000/proxy')

    def test_get_url_without_config(self):
        if 'bridge_url' in os.environ:
            del os.environ['bridge_url']

        config = queryUtility(IBridgeConfig)
        with self.assertRaises(BridgeConfigurationError):
            config.get_url()

    def test_get_ips(self):
        os.environ['bridge_ips'] = '127.0.0.1, 127.0.0.2'
        config = queryUtility(IBridgeConfig)
        self.assertEqual(config.get_bridge_ips(), ['127.0.0.1', '127.0.0.2'])

    def test_get_ips_without_config(self):
        if 'bridge_ips' in os.environ:
            del os.environ['bridge_ips']

        config = queryUtility(IBridgeConfig)
        with self.assertRaises(BridgeConfigurationError):
            config.get_bridge_ips()

    def test_get_client_id(self):
        os.environ['bridge_client_id'] = 'client-one'
        config = getUtility(IBridgeConfig)
        self.assertEqual(config.get_client_id(), 'client-one')

    def test_get_client_id_without_config(self):
        if 'bridge_client_id' in os.environ:
            del os.environ['bridge_client_id']

        config = getUtility(IBridgeConfig)
        with self.assertRaises(BridgeConfigurationError):
            config.get_client_id()
