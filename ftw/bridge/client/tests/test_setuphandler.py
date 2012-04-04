from Products.GenericSetup.context import DirectoryImportContext
from ftw.bridge.client import setuphandlers
from ftw.bridge.client.testing import PLONE_INTEGRATION_TESTING
from ftw.testing import MockTestCase
from plone.testing import z2
import ftw.bridge.client
import os.path


class TestPASPluginSetupHandler(MockTestCase):

    layer = PLONE_INTEGRATION_TESTING

    def test_setuphandler(self):
        default_profile_path = os.path.join(
            os.path.dirname(ftw.bridge.client.__file__),
            'profiles', 'default')

        with z2.zopeApp() as app:
            acl_users = app.acl_users
            self.assertFalse(
                setuphandlers.PLUGIN_ID in acl_users.objectIds())

            setup = DirectoryImportContext(app.acl_users,
                                           default_profile_path)
            setuphandlers.setup_bridge_pas_plugin(setup)

            self.assertTrue(setuphandlers.PLUGIN_ID in acl_users.objectIds())

            # Does not fail on another call
            setuphandlers.setup_bridge_pas_plugin(setup)

    def test_setuphandler_respects_marker_File(self):
        setup = self.mocker.mock()
        filename = 'ftw.bridge.client-setup-bridge-pas-plugin.txt'
        self.expect(setup.readDataFile(filename)).result(None)

        self.replay()

        setuphandlers.setup_bridge_pas_plugin(setup)
