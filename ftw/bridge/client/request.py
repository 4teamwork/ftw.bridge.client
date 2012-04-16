from AccessControl import getSecurityManager
from StringIO import StringIO
from ZODB.POSException import ConflictError
from ftw.bridge.client.exceptions import MaintenanceError
from ftw.bridge.client.interfaces import IBridgeConfig
from ftw.bridge.client.interfaces import IBridgeRequest
from requests.models import Response
from zope.app.component.hooks import getSite
from zope.component import getUtility
from zope.interface import implements
import requests
import urlparse

try:
    import json
except ImportError:
    import simplejson as json


class BridgeRequest(object):
    implements(IBridgeRequest)

    def __call__(self, target, path, method='GET', headers=None, **kwargs):
        """Makes a request to a remote client.
        """
        config = getUtility(IBridgeConfig)

        if config.get_client_id() == target:
            response = self._do_traverse(path, headers, **kwargs)

        else:
            url = self._get_url(config, target, path)
            request_args = kwargs.copy()
            request_args['headers'] = self._get_headers(config, headers)

            response = self._do_request(method, url, **request_args)

        if int(response.status_code) == 503:
            raise MaintenanceError()
        else:
            return response

    def get_json(self, *args, **kwargs):
        """Makes a request to a JSON view on a remote client, return the
        converted python objects.
        """
        return json.loads(self(*args, **kwargs).text)

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

    def _do_request(self, method, url, **kwargs):
        return requests.request(method.lower(), url, **kwargs)

    def _do_traverse(self, path, headers, data=None, **kwargs):
        portal = getSite()

        parsed_path = urlparse.urlparse(path)
        data = dict(urlparse.parse_qsl(parsed_path.query))

        request = portal.REQUEST
        # we need to back up the request data and set them new for the
        # view which is called with the same request (restrictedTraverse)
        ori_form = request.form
        request.form = data

        response = Response()

        try:
            response_data = portal.restrictedTraverse(parsed_path.path)()

        except ConflictError:
            raise

        except Exception as msg:
            response.status_code = 500
            response.raw = StringIO(str(msg))

        else:
            response.status_code = 200
            response.raw = StringIO(response_data)

        finally:
            # restore the request
            request.form = ori_form

        return response
