from ftw.testing.layer import ComponentRegistryLayer
from plone.testing import Layer
import os


class ZCMLLayer(ComponentRegistryLayer):
    """A layer which only sets up the zcml, but does not start a zope
    instance.
    """

    def setUp(self):
        super(ZCMLLayer, self).setUp()

        import ftw.bridge.client.tests
        self.load_zcml_file('tests.zcml', ftw.bridge.client.tests)


ZCML_LAYER = ZCMLLayer()


class BridgeConfigLayer(Layer):

    defaultBases = (ZCML_LAYER,)

    variables = {
        'bridge_url': 'http://bridge/proxy',
        'bridge_ipds': '127.0.0.1, 127.0.0.2',
        'bridge_client_id': 'current-client',
        }

    def setUp(self):
        for key, value in self.variables.items():
            os.environ[key] = value

    def tearDown(self):
        for key in self.variables.keys():
            if key in os.environ:
                del os.environ[key]


BRIDGE_CONFIG_LAYER = BridgeConfigLayer()
