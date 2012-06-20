from AccessControl.SecurityInfo import ClassSecurityInfo
from OFS.Cache import Cacheable
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PluggableAuthService.interfaces import plugins
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from ftw.bridge.client.interfaces import IBridgeConfig
from zope.component import getUtility
from zope.interface import implements
from zope.publisher.browser import BrowserView
import logging


logger = logging.getLogger('ftw.bridge.client.plugin')


class AddBridgePlugin(BrowserView):

    template = ViewPageTemplateFile('templates/add-pas-plugin.pt')

    def __call__(self):

        if 'form.button.Add' in self.request.form:
            name = self.request.form.get('id')
            title = self.request.form.get('title')

            plugin = BridgePlugin(name, title)
            self.context.context[name] = plugin

            self.request.response.redirect(
                self.context.absolute_url() +
                '/manage_workspace?manage_tabs_message=Plugin+added.')

        else:
            return self.template()


class BridgePlugin(BasePlugin, Cacheable):
    """A PAS Plugin that authenticates requests from the bridge.
    """

    implements(plugins.IExtractionPlugin, plugins.IAuthenticationPlugin)

    meta_type = 'Bridge Authentication Plugin'
    security = ClassSecurityInfo()

    def __init__(self, plugin_id, title=None):
        self._setId(plugin_id)
        self.title = title

    security.declarePrivate('extractCredentials')

    def extractCredentials(self, request):
        """Extract Credentials of bridge requests.
        """

        principal = request.get_header('X-BRIDGE-AC', None)
        origin = request.get_header('X-BRIDGE-ORIGIN', None)

        creds = {}

        if origin and principal:
            ip = self._get_request_ip(request)

            creds['id'] = principal
            creds['login'] = principal
            creds['ip'] = ip

            logger.debug('extractCredentials has %r : %r : %r',
                         principal, origin, ip)

        return creds

    security.declarePrivate('authenticateCredentials')

    def authenticateCredentials(self, credentials):
        """Authenticate Credentials for bridge
        """

        extractor = credentials.get('extractor')
        if extractor != self.getId():
            logger.debug('authenticateCredentials: wrong extractor %r != %r',
                         extractor, self.getId())
            return None

        config = getUtility(IBridgeConfig)
        ip = credentials.get('ip')
        allowed_ips = config.get_bridge_ips()

        if ip not in allowed_ips:
            logger.debug('authenticateCredentials: unkown ip %r not in %r',
                         ip, allowed_ips)
            return None

        login = credentials.get('login')
        logger.debug('authenticateCredentials: authenticating %r',
                     login)
        return login, login

    security.declarePrivate('_get_request_ip')

    def _get_request_ip(self, request):
        """Returns the IP address of the host which sent the
        request initally.
        """
        ips = request.environ.get(
            'REMOTE_ADDR',
            request.environ.get('HTTP_X_FORWARDED_FOR'))

        if ips is None or not hasattr(ips, 'split'):
            return ips
        else:
            return ips.split(',')[0].strip()
