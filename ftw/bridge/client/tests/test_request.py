from AccessControl import SecurityManagement
from AccessControl.users import SimpleUser
from ZODB.POSException import ConflictError
from ftw.bridge.client.brain import BrainResultSet
from ftw.bridge.client.exceptions import MaintenanceError
from ftw.bridge.client.interfaces import IBrainRepresentation
from ftw.bridge.client.interfaces import IBridgeRequest
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from ftw.bridge.client.request import replace_placeholder_in_data
from ftw.bridge.client.testing import BRIDGE_CONFIG_LAYER
from ftw.bridge.client.tests.base import RequestAwareTestCase
from mocker import ANY
from unittest2 import TestCase
from zope.app.component.hooks import setSite
from zope.component import getGlobalSiteManager
from zope.component import queryUtility, getUtility
from zope.interface.verify import verifyClass
import json
import urllib2


class TestReplacingPlaceholder(TestCase):

    def test_replace_placeholder_in_data(self):
        data = {
            'foo': u'bar %s baz' % PORTAL_URL_PLACEHOLDER,
            'bar': 2,
            'baz': {
                'sub': PORTAL_URL_PLACEHOLDER},
            'barbaz': [PORTAL_URL_PLACEHOLDER],
            'foobar': (PORTAL_URL_PLACEHOLDER,)}

        replace_placeholder_in_data(data, 'THEURL')
        self.assertEquals(data, {
                'foo': u'bar THEURL baz',
                'bar': 2,
                'baz': {
                    'sub': 'THEURL'},
                'barbaz': ['THEURL'],
                'foobar': ['THEURL']})


class TestBridgeRequestUtility(RequestAwareTestCase):

    layer = BRIDGE_CONFIG_LAYER

    def setUp(self):
        RequestAwareTestCase.setUp(self)

        user = SimpleUser('john.doe', 'pw', [], [])
        SecurityManagement.newSecurityManager(object(), user)

    def tearDown(self):
        SecurityManagement.noSecurityManager()

    def test_component_is_registered(self):
        self.replay()
        utility = queryUtility(IBridgeRequest)
        self.assertNotEqual(utility, None)

    def test_implements_interface(self):
        self.replay()
        utility = getUtility(IBridgeRequest)
        klass = type(utility)

        self.assertTrue(IBridgeRequest.implementedBy(klass))
        verifyClass(IBridgeRequest, klass)

    def test_request_path(self):
        response = self._create_response()
        self._expect_request(
            url='http://bridge/proxy/target-client/path/to/@@something'
            ).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        self.assertEqual(
            utility('target-client', 'path/to/@@something'),
            response)

    def test_request_path_with_leading_slash(self):
        response = self._create_response()
        self._expect_request(
            url='http://bridge/proxy/target-client/@@something'
            ).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        self.assertEqual(
            utility('target-client', '/@@something'),
            response)

    def test_request_default_headers(self):
        response = self._create_response()
        self._expect_request(
            headers={'X-BRIDGE-ORIGIN': 'current-client',
                     'X-BRIDGE-AC': 'john.doe'}
            ).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        self.assertEqual(
            utility('target-client', '@@something2'),
            response)

    def test_request_custom_headers(self):
        response = self._create_response()
        self._expect_request(
            headers={'X-BRIDGE-ORIGIN': 'current-client',
                     'X-BRIDGE-AC': 'john.doe',
                     'X-CUSTOM-HEADER': 'some data'}
            ).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        headers = {'X-CUSTOM-HEADER': 'some data'}
        self.assertEqual(len(headers), 1)
        self.assertEqual(
            utility('target-client', '@@something',
                    headers={'X-CUSTOM-HEADER': 'some data'}),
            response)
        self.assertEqual(len(headers), 1)

    def test_passed_data(self):
        response = self._create_response()
        self._expect_request(data={'foo': 'bar'}).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)
        self.assertEqual(
            utility('target-client', '@@something',
                    data={'foo': 'bar'}),
            response)

    def test_maintenance_response_raises_exception(self):
        self._expect_request().throw(urllib2.HTTPError(
                'url', 503, 'Service Unavailable', None, None))

        self.replay()
        utility = getUtility(IBridgeRequest)

        with self.assertRaises(MaintenanceError):
            utility('target-client', '@@something')

    def test_get_json(self):
        response = self._create_response(raw='[{"foo": "bar"}]')
        self._expect_request(
            url='http://bridge/proxy/target-client/@@json-view',
            ).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)

        self.assertEqual(
            utility.get_json('target-client', '@@json-view'),
            [{'foo': 'bar'}])

    def test_search_catalog(self):
        response_data = [
            {'Title': 'Foo',
             '_url': 'https://target-client/foo',
             'portal_type': 'Folder'}]
        query = {'portal_type': ['Folder']}

        response = self._create_response(raw=json.dumps(response_data))
        response.headers = {'X-total_results_length': '1'}
        url = 'http://bridge/proxy/foo/@@bridge-search-catalog'

        self._expect_request(
            url=url,
            data={'query': json.dumps({'portal_type': ['Folder'],
                                       'batching_start': 0}),
                  'limit': 50}).result(response)

        self.replay()
        utility = getUtility(IBridgeRequest)
        results = utility.search_catalog('foo', query)

        self.assertEqual(type(results), BrainResultSet)
        self.assertEqual(len(results), 1)
        brain = results[0]
        self.assertTrue(IBrainRepresentation.providedBy(brain))
        self.assertEqual(brain.getURL(), 'https://target-client/foo')
        self.assertEqual(brain.portal_type, 'Folder')
        self.assertEqual(brain.Title, 'Foo')

    def test_get_json_error(self):
        self._expect_request().throw(
            urllib2.URLError('Connection failed'))

        site = self.stub()
        self.expect(site.getSiteManager()).call(getGlobalSiteManager)
        self.expect(site.error_log.raising(ANY))

        self.replay()

        utility = getUtility(IBridgeRequest)
        setSite(site)

        self.assertEqual(
            utility.get_json('target-client',
                             'path/to/@@something', silent=True),
            None)

    def test_traversing(self):
        site = self.stub()
        self.expect(site.getSiteManager()).call(getGlobalSiteManager)
        self.expect(site.absolute_url()).result('http://nohost/plone')

        request = self.create_dummy(
            form={'ori': 'formdata'},
            RESPONSE=self.create_dummy(
                headers={}))
        self.expect(site.REQUEST).result(request)

        assertion_data = self.create_dummy()

        def view_method():
            assertion_data.form = request.form.copy()
            return 'the url %s@@view should be replaced' % (
                PORTAL_URL_PLACEHOLDER)

        with self.mocker.order():
            # test 1
            self.expect(site.restrictedTraverse('baz/@@view')()).call(
                view_method)
            # test 2
            self.expect(site.restrictedTraverse('baz/@@view')()).throw(
                Exception('failed'))
            # test 3
            self.expect(site.restrictedTraverse('baz/@@view')()).throw(
                ConflictError())

        self.replay()

        utility = getUtility(IBridgeRequest)
        setSite(site)

        # test 1
        response = utility(
            'current-client',
            'baz/@@view?foo=bar&baz=%s' % PORTAL_URL_PLACEHOLDER,
            data={'url': PORTAL_URL_PLACEHOLDER})
        self.assertEqual(assertion_data.form, {
                'foo': 'bar',
                'url': 'http://nohost/plone/',
                'baz': 'http://nohost/plone/'})
        self.assertEqual(request.form, {'ori': 'formdata'})
        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.read(),
            'the url http://nohost/plone/@@view should be replaced')

        # test 2
        with self.assertRaises(urllib2.HTTPError) as cm:
            response = utility('current-client', 'baz/@@view?foo=bar')
        response = cm.exception
        self.assertEqual(request.form, {'ori': 'formdata'})
        self.assertEqual(response.code, 500)
        self.assertIn(response.read(), 'failed')

        # test 3
        with self.assertRaises(ConflictError):
            utility('current-client', 'baz/@@view?foo=bar')

    def test_silent_error_is_logged(self):
        self._expect_request().throw(
            urllib2.URLError('Connection failed'))

        site = self.stub()
        self.expect(site.getSiteManager()).call(getGlobalSiteManager)
        self.expect(site.error_log.raising(ANY))

        self.replay()

        utility = getUtility(IBridgeRequest)
        setSite(site)

        self.assertEqual(
            utility('target-client', 'path/to/@@something', silent=True),
            None)

    def test_nonsilent_error_is_reraised(self):
        self._expect_request().throw(
            urllib2.URLError('Connection failed'))

        self.replay()
        utility = getUtility(IBridgeRequest)
        with self.assertRaises(urllib2.URLError):
            utility('target-client', 'path/to/@@something')
