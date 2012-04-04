from ftw.bridge.client.exceptions import BridgeConfigurationError
from ftw.bridge.client.interfaces import IBridgeConfig
from zope.interface import implements
import os


class BridgeConfig(object):
    implements(IBridgeConfig)

    def get_url(self):
        url = os.environ.get('bridge_url', None)
        if url is None:
            raise BridgeConfigurationError()
        return url

    def get_bridge_ips(self):
        ips = os.environ.get('bridge_ips', None)
        if ips is None:
            raise BridgeConfigurationError()

        return [ip.strip() for ip in ips.strip().split(',')]

    def get_client_id(self):
        id_ = os.environ.get('bridge_client_id', None)
        if id_ is None:
            raise BridgeConfigurationError()

        return id_.strip()
