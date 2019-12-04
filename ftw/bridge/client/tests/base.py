from StringIO import StringIO
from ftw.testing import MockTestCase
from mock import patch
from contextlib import contextmanager
import urllib
import urllib2


class RequestAwareTestCase(MockTestCase):

    def _create_response(self, status_code=200, raw='response data',
                         total_length=None):
        data = StringIO(raw)
        response = self.create_dummy(
            code=status_code,
            fp=data,
            read=data.read,
            headers={})
        return response

    @contextmanager
    def patch(self, response=None, error=None):
        http_error = urllib2.HTTPError
        url_error = urllib2.URLError

        with patch('ftw.bridge.client.request.urllib2') as mocked_urllib2:
            self._urllib2 = mocked_urllib2
            opener = self.mock()
            self._urllib2.HTTPError = http_error
            self._urllib2.URLError = url_error

            if response:
                opener.open.return_value = response
            if error:
                opener.open.side_effect = error

            self._urllib2.build_opener.return_value = opener

            self._urllib2.Request = self.mock()
            yield self._urllib2

    def assertRquest(self, position, value):
        self.assertEquals(self._urllib2.Request.call_args[0][position], value)

    def assertUrl(self, value):
        self.assertRquest(0, value)

    def assertData(self, value):
        if isinstance(value, dict):
            value = urllib.urlencode(value)
        self.assertRquest(1, value)

    def assertHeaders(self, value):
        self.assertRquest(2, value)
