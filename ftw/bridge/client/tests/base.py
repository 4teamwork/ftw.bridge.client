from StringIO import StringIO
from ftw.testing import MockTestCase
from mocker import ANY, ARGS, KWARGS
import urllib


class RequestAwareTestCase(MockTestCase):

    def setUp(self):
        MockTestCase.setUp(self)

        self.urllib2 = self.mocker.replace('urllib2')
        # Let the urllib2 not do any requests at all while
        # testing. We do this by expecting any request call zero times.
        self.expect(self.urllib2.build_opener(ARGS, KWARGS)).count(0)
        self.expect(self.urllib2.Request(ARGS, KWARGS)).count(0)

    def _create_response(self, status_code=200, raw='response data',
                         total_length=None):
        data = StringIO(raw)
        response = self.create_dummy(
            code=status_code,
            fp=data,
            read=data.read,
            headers={})
        return response

    def _expect_request(self, url=ANY, headers=ANY, data=None):
        data = data and urllib.urlencode(data) or ANY
        request = self.mocker.mock()
        self.expect(self.urllib2.Request(
                url,
                data,
                headers)).result(request)
        opener = self.mocker.mock()
        self.expect(self.urllib2.build_opener(ANY)).result(opener)
        return self.expect(opener.open(request))
