from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces import plugins
from ftw.bridge.client.plugin import BridgePlugin


PLUGIN_ID = 'ftw-bridge'


def setup_bridge_pas_plugin(setup):
    if setup.readDataFile(
        'ftw.bridge.client-setup-bridge-pas-plugin.txt') is None:
        return

    acl_users = getToolByName(setup.getSite(), 'acl_users')

    if PLUGIN_ID in acl_users.objectIds():
        return

    plugin = BridgePlugin(PLUGIN_ID)
    acl_users._setObject(plugin.getId(), plugin)
    # acl_users[PLUGIN_ID] = plugin
    plugin = acl_users.get(PLUGIN_ID)

    # activate PAS plugin handlers
    plugin_interfaces = [plugins.IAuthenticationPlugin.__name__,
                         plugins.IExtractionPlugin.__name__]
    plugin.manage_activateInterfaces(plugin_interfaces)
