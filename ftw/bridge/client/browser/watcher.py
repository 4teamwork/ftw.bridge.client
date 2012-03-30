from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from ftw.bridge.client.portlets.watcher import Assignment
from persistent.dict import PersistentDict
from plone.portlets.constants import USER_CATEGORY
from plone.portlets.interfaces import IPortletManager
from zope.component import getUtility


class  AddWatcherPortlet(BrowserView):

    def __call__(self):
        origin = self.request.get_header('X-BRIDGE-ORIGIN')
        path = self.request.get('path')

        column_manager = getUtility(IPortletManager, name='plone.dashboard1')
        membership_tool = getToolByName(self.context, 'portal_membership')
        member = membership_tool.getAuthenticatedMember()

        if not member or not member.getId():
            raise Exception(
                'Could not find userid.')

        userid = member.getId()
        users_category = column_manager.get(USER_CATEGORY)
        column = users_category.get(userid, None)
        if not column:
            column = PersistentDict()
            users_category[userid] = column

        portlet_id = self._generate_portlet_id(column)

        column[portlet_id] = Assignment(client_id=origin, path=path)

        return 'OK'

    def _generate_portlet_id(self, column, base='watcher'):
        if base not in column:
            return base

        counter = 0
        while True:
            counter += 1
            id = base + str(counter)

            if id not in column:
                return id
