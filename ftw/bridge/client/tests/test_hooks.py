from ftw.bridge.client import hooks
from ftw.bridge.client.testing import PLONE_INTEGRATION_TESTING
from ftw.testing import MockTestCase
from Products.CMFCore.utils import getToolByName


class TestPASPluginSetupHandler(MockTestCase):

    layer = PLONE_INTEGRATION_TESTING

    def test_setuphandler(self):
        acl_users = getToolByName(self.layer['portal'], 'acl_users')
        self.assertFalse(hooks.PLUGIN_ID in acl_users.objectIds())

        hooks.install_pas_plugin(self.layer['portal'])
        self.assertTrue(hooks.PLUGIN_ID in acl_users.objectIds())

        # Does not fail on another call
        hooks.install_pas_plugin(self.layer['portal'])
