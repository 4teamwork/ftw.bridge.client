from AccessControl import getSecurityManager
from StringIO import StringIO
from ZODB.POSException import ConflictError
from ftw.bridge.client.exceptions import MaintenanceError
from ftw.bridge.client.interfaces import IBrainSerializer
from ftw.bridge.client.interfaces import IBridgeConfig
from ftw.bridge.client.interfaces import IBridgeRequest
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from ftw.bridge.client.utils import json
from zope.app.component.hooks import getSite
from zope.component import getUtility
from zope.interface import implements
import os.path
import sys
import types
import urllib
import urllib2
import urlparse


def replace_placeholder_in_data(data, public_url):
    if isinstance(data, types.StringTypes):
        return data.replace(PORTAL_URL_PLACEHOLDER, public_url)

    elif isinstance(data, types.DictType):
        for key, value in data.items():
            data[key] = replace_placeholder_in_data(value, public_url)
        return data

    elif isinstance(data, (types.ListType, types.TupleType)):
        new = []
        for value in data:
            new.append(replace_placeholder_in_data(value, public_url))
        return new

    else:
        return data


class BridgeRequest(object):
    implements(IBridgeRequest)

    def __call__(self, target, path, headers=None, data=None, silent=False):
        """Makes a request to a remote client.
        """
        try:
            return self._request(target, path, headers, data)

        except (urllib2.HTTPError, urllib2.URLError), exc:
            if getattr(exc, 'code', None) == 503:
                raise MaintenanceError()

            elif silent:
                getSite().error_log.raising(sys.exc_info())
                return None

            else:
                raise

    def get_json(self, *args, **kwargs):
        """Makes a request to a JSON view on a remote client, return the
        converted python objects.
        """
        response = self(*args, **kwargs)
        if response is None:
            return None
        else:
            return json.loads(response.read())

    def search_catalog(self, target, query, limit=50, batching_start=0):
        path = '@@bridge-search-catalog'
        query['batching_start'] = batching_start
        data = {'query': json.dumps(query),
                'limit': limit}

        response = self(target, path, data=data)
        data = json.loads(response.read())
        total_length = int(response.headers.get(
                'X-total_results_length', '0'))

        serializer = getUtility(IBrainSerializer)
        return serializer.deserialize_brains(data, total_length)

    def _get_url(self, config, target, path):
        if path.startswith('/'):
            path = path[1:]
        return '/'.join((config.get_url(), target, path))

    def _get_headers(self, config, additional_headers):
        headers = {
            'X-BRIDGE-ORIGIN': config.get_client_id(),
            'X-BRIDGE-AC': self._get_current_userid()}

        if additional_headers:
            headers.update(additional_headers)

        return headers

    def _get_current_userid(self):
        return getSecurityManager().getUser().getId()

    def _request(self, target, path, headers, data):
        config = getUtility(IBridgeConfig)
        if config.get_client_id() == target:
            return self._do_traverse(path, headers, data)

        else:
            url = self._get_url(config, target, path)
            headers = self._get_headers(config, headers)
            return self._do_request(url, headers, data)

    def _do_request(self, url, headers, data):
        handler = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(handler)

        if data:
            data = urllib.urlencode(data)

        request = urllib2.Request(url, data, headers)
        return opener.open(request)

    def _do_traverse(self, path, headers, data):
        portal = getSite()
        public_url = portal.absolute_url() + '/'

        parsed_path = urlparse.urlparse(path)
        form_data = dict(urlparse.parse_qsl(parsed_path.query))
        if data:
            form_data.update(data)
        replace_placeholder_in_data(form_data, public_url)

        request = portal.REQUEST
        # we need to back up the request data and set them new for the
        # view which is called with the same request (restrictedTraverse)
        ori_form = request.form
        ori_response_headers = request.RESPONSE.headers
        request.RESPONSE.headers = {}
        request.form = form_data

        response_url = os.path.join(portal.absolute_url(), parsed_path.path)
        response = None

        try:
            response_data = portal.restrictedTraverse(parsed_path.path)()

        except ConflictError:
            raise

        except Exception, exc:
            # restore the request
            request.form = ori_form
            request.RESPONSE.headers = ori_response_headers

            code = 500
            msg = str(exc)
            hdrs = {}
            fp = StringIO(msg)
            raise urllib2.HTTPError(response_url, code, msg, hdrs, fp)

        else:
            # restore the request
            response_headers = request.RESPONSE.headers
            request.form = ori_form
            request.RESPONSE.headers = ori_response_headers

            response_data = StringIO(response_data.replace(
                    PORTAL_URL_PLACEHOLDER, public_url))

            response = urllib.addinfourl(
                response_data, headers=response_headers,
                url=response_url, code=200)

        return response
