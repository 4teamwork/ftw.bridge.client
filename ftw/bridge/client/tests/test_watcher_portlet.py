from ftw.bridge.client.portlets import watcher
from ftw.bridge.client.testing import ZCML_LAYER
from ftw.testing import MockTestCase
from plone.app.portlets.interfaces import IPortletTypeInterface
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletRenderer
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.component.interfaces import IFactory
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserView


class TestWatcherPortlet(MockTestCase):

    layer = ZCML_LAYER

    def test_portlet_type_registered(self):
        portlet_interface = queryUtility(
            IPortletTypeInterface, name='ftw.bridge.client.watcher_portlet')
        self.assertEqual(portlet_interface, watcher.IWatcherPortlet)

    def test_portlet_factory_registerd(self):
        factory = queryUtility(
            IFactory, name='ftw.bridge.client.watcher_portlet')
        self.assertNotEquals(factory, None)

    def test_renderer(self):
        context = self.create_dummy()
        request = self.stub_request()
        view = self.providing_stub(IBrowserView)
        manager = self.providing_stub(IPortletManager)
        assignment = watcher.Assignment('client-one', '@@watch')

        plone_portal_state = self.stub()
        self.mock_adapter(plone_portal_state, IBrowserView,
                          (Interface, Interface), name='plone_portal_state')
        self.expect(plone_portal_state(context, request)).result(
            plone_portal_state)
        self.expect(plone_portal_state.anonymous()).result(False)

        self.replay()

        renderer = getMultiAdapter(
            (context, request, view, manager, assignment), IPortletRenderer)
        self.assertNotEqual(renderer, None)
