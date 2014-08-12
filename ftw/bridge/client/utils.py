from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite

try:
    import json
except ImportError:
    import simplejson as json


def get_object_url(obj):
    """Returns the url to this object using, replacing the site url with a
    placeholder replaced with the public URL by the bridge.
    """
    portal_url = getToolByName(obj, 'portal_url')() + '/'
    return obj.absolute_url().replace(portal_url, PORTAL_URL_PLACEHOLDER)


def get_brain_url(brain):
    """Returns the brain to this object using, replacing the site url with a
    placeholder replaced with the public URL by the bridge.
    """
    portal_url = getToolByName(getSite(), 'portal_url')() + '/'
    return brain.getURL().replace(portal_url, PORTAL_URL_PLACEHOLDER)


def to_utf8_recursively(data):
    if isinstance(data, unicode):
        return data.encode('utf-8')
    elif isinstance(data, list):
        return map(to_utf8_recursively, data)
    elif isinstance(data, dict):
        return dict(map(lambda item: map(to_utf8_recursively, item),
                        data.items()))
    else:
        return data
