from ftw.testing.layer import ComponentRegistryLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_INTEGRATION_TESTING
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
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


class PloneTestingLayer(PloneSandboxLayer):

    defaultBases = (PLONE_INTEGRATION_TESTING,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import ftw.bridge.client
        self.loadZCML(package=ftw.bridge.client)


PLONE_TESTING_LAYER = PloneTestingLayer()


class IntegrationTestingLayer(PloneTestingLayer):

    defaultBases = (PLONE_INTEGRATION_TESTING,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import ftw.bridge.client
        self.loadZCML(package=ftw.bridge.client)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.bridge.client:default')


INTEGRATION_FIXTURE = IntegrationTestingLayer()
INTEGRATION_TESTING = IntegrationTesting(
    bases=(INTEGRATION_FIXTURE,), name='ftw.bridge.client:Integration')


class ExampleContentLayer(PloneSandboxLayer):

    defaultBases = (INTEGRATION_TESTING,)

    def setUpPloneSite(self, portal):
        setRoles(portal, TEST_USER_ID, ['Manager'])
        self['folder'] = folder = portal.get(portal.invokeFactory(
                'Folder', 'feed-folder', title='Feed folder'))
        folder.invokeFactory('Document', 'page', title='The page')
        setRoles(portal, TEST_USER_ID, ['Member'])


EXAMPLE_CONTENT_LAYER = ExampleContentLayer()
