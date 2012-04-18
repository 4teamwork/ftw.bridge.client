from AccessControl import getSecurityManager
from StringIO import StringIO
from ZODB.POSException import ConflictError
from ftw.bridge.client.exceptions import MaintenanceError
from ftw.bridge.client.interfaces import IBridgeConfig
from ftw.bridge.client.interfaces import IBridgeRequest
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from ftw.bridge.client.utils import json
from requests.exceptions import RequestException
from requests.models import Response
from zope.app.component.hooks import getSite
from zope.component import getUtility
from zope.interface import implements
import requests
import sys
import types
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

    def __call__(self, target, path, method='GET', headers=None,
                 silent=False, **kwargs):
        """Makes a request to a remote client.
        """
        config = getUtility(IBridgeConfig)

        if config.get_client_id() == target:
            response = self._do_traverse(path, headers, **kwargs)

        else:
            url = self._get_url(config, target, path)
            request_args = kwargs.copy()
            request_args['headers'] = self._get_headers(config, headers)

            try:
                response = self._do_request(method, url, **request_args)
            except RequestException:
                if silent:
                    getSite().error_log.raising(sys.exc_info())
                    return None
                else:
                    raise

        if int(response.status_code) == 503:
            raise MaintenanceError()
        else:
            return response

    def get_json(self, *args, **kwargs):
        """Makes a request to a JSON view on a remote client, return the
        converted python objects.
        """
        response = self(*args, **kwargs)
        if response is None or response.status_code != 200:
            return None
        else:
            return json.loads(response.text)

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
        request.form = form_data

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
            response_data = response_data.replace(
                PORTAL_URL_PLACEHOLDER, public_url)
            response.raw = StringIO(response_data)

        finally:
            # restore the request
            request.form = ori_form

        return response
