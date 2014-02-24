from Products.CMFCore.utils import getToolByName
from StringIO import StringIO
from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from ftw.testing.layer import ComponentRegistryLayer
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FUNCTIONAL_TESTING
from plone.app.testing import PLONE_INTEGRATION_TESTING
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
from plone.testing import Layer
import os


CONFIG_VARIABLES = {
        'bridge_url': 'http://bridge/proxy',
        'bridge_ipds': '127.0.0.1, 127.0.0.2',
        'bridge_client_id': 'current-client',
        }


def setup_config():
    for key, value in CONFIG_VARIABLES.items():
        os.environ[key] = value


def teardown_config():
    for key in CONFIG_VARIABLES.keys():
        if key in os.environ:
            del os.environ[key]


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

    def setUp(self):
        setup_config()

    def tearDown(self):
        teardown_config()


BRIDGE_CONFIG_LAYER = BridgeConfigLayer()


class PloneTestingLayer(PloneSandboxLayer):

    defaultBases = (PLONE_INTEGRATION_TESTING,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import ftw.bridge.client
        self.loadZCML(package=ftw.bridge.client)


PLONE_TESTING_LAYER = PloneTestingLayer()


class IntegrationTestingLayer(PloneTestingLayer):

    defaultBases = (PLONE_INTEGRATION_TESTING,
                    BUILDER_LAYER)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import ftw.bridge.client
        self.loadZCML(package=ftw.bridge.client)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.bridge.client:default')

        mtool = getToolByName(portal, 'portal_membership')
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory('Folder', 'Members', title='Members')
        mtool.setMemberareaCreationFlag()
        mtool.createMemberarea(TEST_USER_ID)
        setRoles(portal, TEST_USER_ID, ['Member'])


INTEGRATION_FIXTURE = IntegrationTestingLayer()
INTEGRATION_TESTING = IntegrationTesting(
    bases=(INTEGRATION_FIXTURE,), name='ftw.bridge.client:Integration')


class FunctionTestingLayer(PloneTestingLayer):

    defaultBases = (PLONE_FUNCTIONAL_TESTING, INTEGRATION_FIXTURE)


FUNCTIONAL_FIXTURE = FunctionTestingLayer()
FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FUNCTIONAL_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name='ftw.bridge.client:Functional')


class ExampleContentLayer(PloneSandboxLayer):

    defaultBases = (INTEGRATION_TESTING,)

    def setUpPloneSite(self, portal):
        setup_config()

        setRoles(portal, TEST_USER_ID, ['Manager'])
        self['folder'] = folder = portal.get(portal.invokeFactory(
                'Folder', 'feed-folder', title='Feed folder'))
        folder.invokeFactory('Document', 'page',
                             title='The page with uml\xc3\xa4uts')

        filedata = StringIO('foo bar')
        self['file'] = portal.get(
            portal.invokeFactory('File', 'file', file=filedata,
                                 title='the file'))

        setRoles(portal, TEST_USER_ID, ['Member'])

    def tearDownPloneSite(self, portal):
        teardown_config()


EXAMPLE_CONTENT_LAYER = ExampleContentLayer()
