from ftw.bridge.client.tabbed import interfaces
from ftw.bridge.client.tabbed.components import BridgeCatalogTableSource
from ftw.bridge.client.testing import BRIDGE_CONFIG_LAYER
from ftw.bridge.client.tests.base import RequestAwareTestCase
from ftw.table.interfaces import ITableSource
from zope.component import queryMultiAdapter
import json


class TestTableSource(RequestAwareTestCase):

    layer = BRIDGE_CONFIG_LAYER

    def test_component_registered(self):
        config = self.providing_stub(
            interfaces.IBridgeCatalogTableSourceConfig)
        request = self.create_dummy()

        self.replay()

        component = queryMultiAdapter((config, request), ITableSource)
        self.assertNotEqual(component, None)
        self.assertEqual(type(component), BridgeCatalogTableSource)

    def test_implements_interface(self):
        self.replay()
        self.assertTrue(ITableSource.implementedBy(BridgeCatalogTableSource))

    def test_search_results_requests_bridge(self):
        config = self.providing_stub(
            interfaces.IBridgeCatalogTableSourceConfig)
        self.expect(config.bridge_remote_client_id).result('other-client')
        self.expect(config.bridge_remove_path).result(False)
        self.expect(config.batching_pagesize).result(50)
        self.expect(config.pagesize).result(50)
        self.expect(config.batching_current_page).result(1)
        request = self.create_dummy(
            RESPONSE=self.create_dummy(
                headers={}))

        response_data = [
            {'Title': 'Foo',
             '_url': 'https://target-client/foo',
             'portal_type': 'Folder'},
            {'Title': 'Bar',
             '_url': 'https://target-client/bar',
             'portal_type': 'Folder'}]

        query = {'portal_type': ['Folder']}

        response = self._create_response(raw=json.dumps(response_data))
        url = 'http://bridge/proxy/other-client/@@bridge-search-catalog'

        self._expect_request(
            url=url,
            data={'query': json.dumps({'portal_type': ['Folder'],
                                       'batching_start': 0}),
                  'limit': 50}).result(response)

        self.replay()
        component = queryMultiAdapter((config, request), ITableSource)
        results = component.search_results(query)
        self.assertEqual(len(results), 2)

    def test_search_results_fails_when_wrong_configured(self):
        config = self.providing_stub(
            interfaces.IBridgeCatalogTableSourceConfig)
        self.expect(config.bridge_remote_client_id).result(None)
        request = self.create_dummy()

        self.replay()
        component = queryMultiAdapter((config, request), ITableSource)
        with self.assertRaises(ValueError) as cm:
            component.search_results({})
        self.assertIn(
            'defines no bridge_remote_client_id',
            str(cm.exception))

    def test_path_removed(self):
        config = self.providing_stub(
            interfaces.IBridgeCatalogTableSourceConfig)
        self.expect(config.bridge_remote_client_id).result('other-client')
        self.expect(config.bridge_remove_path).result(True)
        self.expect(config.batching_pagesize).result(50)
        self.expect(config.pagesize).result(50)
        self.expect(config.batching_current_page).result(1)
        request = self.create_dummy()

        query = {'portal_type': ['Folder'],
                 'path': '/Plone'}

        response = self._create_response(raw='[]')
        url = 'http://bridge/proxy/other-client/@@bridge-search-catalog'

        self._expect_request(
            url=url,
            data={'query': json.dumps({'portal_type': ['Folder'],
                                       'batching_start': 0}),
                  'limit': 50}).result(response)

        self.replay()
        component = queryMultiAdapter((config, request), ITableSource)
        component.search_results(query)
