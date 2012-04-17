from AccessControl import SecurityManagement
from Products.CMFCore.utils import getToolByName
from ftw.bridge.client.portlets import watcher
from ftw.bridge.client.testing import INTEGRATION_TESTING
from plone.portlets.constants import USER_CATEGORY
from plone.portlets.interfaces import IPortletManager
from unittest2 import TestCase
from zope.component import getUtility
from zope.component import queryMultiAdapter


class TestAddWatcherPortletView(TestCase):

    layer = INTEGRATION_TESTING

    def _get_portlets(self, manager='plone.dashboard1'):
        context = self.layer['portal']
        column_manager = getUtility(IPortletManager, name=manager)
        membership_tool = getToolByName(context, 'portal_membership')
        userid = membership_tool.getAuthenticatedMember().getId()
        user_category = column_manager.get(USER_CATEGORY, None)
        if not user_category:
            return []

        column = user_category.get(userid, None)
        if not column:
            return []

        portlets = []
        for portlet in column.values():
            if watcher.IWatcherPortlet.providedBy(portlet):
                portlets.append(portlet)

        return portlets

    def test_component_is_registered(self):
        portal = self.layer['portal']
        request = self.layer['request']
        self.assertNotEquals(
            queryMultiAdapter((portal, request), name='add-watcher-portlet'),
            None)

    def test_add_portlet(self):
        portal = self.layer['portal']
        request = self.layer['request']

        request.environ['HTTP_X_BRIDGE_ORIGIN'] = 'client-one'
        request.form['path'] = '@@watcher-feed?uid=567891234'

        view = queryMultiAdapter((portal, request),
                                 name='add-watcher-portlet')

        self.assertEqual(len(self._get_portlets()), 0)

        self.assertEqual(view(), 'OK')
        portlets = self._get_portlets()
        self.assertEqual(len(portlets), 1)
        self.assertEqual(portlets[0].client_id, 'client-one')
        self.assertEqual(portlets[0].path, '@@watcher-feed?uid=567891234')

        self.assertEqual(view(), 'OK')
        self.assertEqual(len(self._get_portlets()), 2)

        self.assertEqual(view(), 'OK')
        self.assertEqual(len(self._get_portlets()), 3)

    def test_add_portlet_fails_with_anonymous(self):
        portal = self.layer['portal']
        request = self.layer['request']

        request.environ['HTTP_X_BRIDGE_ORIGIN'] = 'client-one'
        request.form['path'] = '@@watcher-feed?uid=567891234'

        sm = SecurityManagement.getSecurityManager()
        SecurityManagement.noSecurityManager()

        try:
            view = queryMultiAdapter((portal, request),
                                     name='add-watcher-portlet')
            with self.assertRaises(Exception) as cm:
                view()
            self.assertEqual(str(cm.exception), 'Could not find userid.')

        finally:
            SecurityManagement.setSecurityManager(sm)
