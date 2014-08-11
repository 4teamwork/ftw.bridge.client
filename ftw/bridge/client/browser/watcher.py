from datetime import datetime
from ftw.bridge.client import _
from ftw.bridge.client.exceptions import MaintenanceError
from ftw.bridge.client.interfaces import IBridgeRequest
from ftw.bridge.client.interfaces import MAINTENANCE_ERROR_MESSAGE
from ftw.bridge.client.portlets.watcher import Assignment
from ftw.bridge.client.utils import get_brain_url
from ftw.bridge.client.utils import get_object_url
from ftw.bridge.client.utils import json
from ftw.bridge.client.utils import to_utf8_recursively
from plone.app.portlets.utils import assignment_from_key
from plone.app.portlets.utils import assignment_mapping_from_key
from plone.portlets.constants import USER_CATEGORY
from plone.portlets.utils import unhashPortletInfo
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.PloneBatch import Batch
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getMultiAdapter
from zope.component import getUtility
import time


WATCHER_PORTLET_LIMIT = 5
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class WatchAction(BrowserView):
    """Creates a "watcher" portlet on the client with the ID (or alias)
    "dashboard" through the bridge.
    """

    def __call__(self):
        uid = self.context.UID
        if callable(uid):
            uid = uid()

        feed_path = '@@watcher-feed?uid=%s' % uid

        requester = getUtility(IBridgeRequest)
        try:
            response = requester('dashboard', '@@add-watcher-portlet',
                                 data={'path': feed_path},
                                 silent=True)

        except MaintenanceError:
            IStatusMessage(self.request).addStatusMessage(
                MAINTENANCE_ERROR_MESSAGE, type='error')

        else:
            if response is None or response.code != 200:
                IStatusMessage(self.request).addStatusMessage(
                    _(u'error_portlet_creation_failed',
                      default=u'The dashboard portlet could not be created.'),
                    type='error')

            else:
                IStatusMessage(self.request).addStatusMessage(
                    _(u'info_msg_portlet_created',
                      default=u'A dashboard portlet was created.'),
                    type='info')

        referer = self.request.environ.get('HTTP_REFERER')
        if referer:
            self.request.RESPONSE.redirect(referer)

        else:
            state = getMultiAdapter((self.context, self.request),
                                    name='plone_context_state')
            self.request.RESPONSE.redirect(state.view_url())


class AddWatcherPortlet(BrowserView):

    def __call__(self):
        mapping = self._get_assignment_mapping()
        data = self._get_portlet_data()
        self._add_portlet(mapping, data)
        return 'OK'

    def _get_portlet_data(self):
        return {'client_id': self.request.get_header('X-BRIDGE-ORIGIN'),
                'path': self.request.get('path')}

    def _get_assignment_mapping(self):
        membership_tool = getToolByName(self.context, 'portal_membership')
        member = membership_tool.getAuthenticatedMember()

        if not member.getId():
            raise Exception(
                'Could not find userid.')

        userid = member.getId()

        return assignment_mapping_from_key(
            context=self.context,
            manager_name='plone.dashboard1',
            category=USER_CATEGORY,
            key=userid,
            create=True)

    def _add_portlet(self, mapping, data):
        portlet_id = self._generate_portlet_id(mapping)
        mapping[portlet_id] = Assignment(**data)
        mapping[portlet_id].__name__ = portlet_id
        return mapping[portlet_id]

    def _generate_portlet_id(self, column, base='watcher'):
        if base not in column:
            return base

        counter = 0
        while True:
            counter += 1
            id_ = base + str(counter)

            if id_ not in column:
                return id_


class WatcherFeed(BrowserView):

    def __call__(self):
        uid = self.request.get('uid')
        reference_catalog = getToolByName(self.context, 'reference_catalog')
        obj = reference_catalog.lookupObject(uid)
        data = self.get_data(obj)
        return json.dumps(data)

    def get_data(self, obj):
        return {
            'title': obj.Title().decode('utf-8'),
            'items': list(self.get_items(obj)),
            'details_url': '%s/@@watcher-recently-modified' % (
                get_object_url(obj))}

    def get_items(self, obj):
        brains = self.query_catalog(obj)
        for brain in brains:
            yield self.get_item_data(brain)

    def query_catalog(self, obj, limit=WATCHER_PORTLET_LIMIT):
        catalog = getToolByName(self.context, 'portal_catalog')

        return catalog(path='/'.join(obj.getPhysicalPath()),
                       sort_on='modified',
                       sort_order='reverse',
                       sort_limit=limit)

    def get_item_data(self, brain):
        return {
            'title': to_utf8_recursively(brain.Title),
            'url': get_brain_url(brain),
            'modified': brain.modified.strftime(DATETIME_FORMAT),
            'portal_type': brain.portal_type,
            'cssclass': u'',
            }


class AjaxLoadPortletData(BrowserView):

    def __call__(self):
        portlet = self._get_portlet()
        try:
            data = self._get_data(portlet)
        except MaintenanceError:
            return '"MAINTENANCE"'

        data = self._localize_dates(data)
        return json.dumps(data)

    def _get_portlet(self):
        portlet_hash = self.request.get('hash')

        info = unhashPortletInfo(portlet_hash)

        return assignment_from_key(
            context=self.context,
            manager_name=info['manager'],
            category=info['category'],
            key=info['key'],
            name=info['name'])

    def _get_data(self, portlet):
        requester = getUtility(IBridgeRequest)
        return requester.get_json(portlet.client_id, portlet.path)

    def _localize_dates(self, data):
        translation = getToolByName(self.context, 'translation_service')
        localize_time = translation.ulocalized_time

        for item in data.get('items'):
            if item.get('modified'):
                date = datetime(*(time.strptime(
                            item['modified'], DATETIME_FORMAT)[0:6]))
                item['modified'] = localize_time(date, long_format=False)

        return data


class RecentlyModified(BrowserView):
    """A local recently modified view.
    """

    def __init__(self, *args, **kwargs):
        super(RecentlyModified, self).__init__(*args, **kwargs)
        self.batched_results = None

    def __call__(self):
        self.update()
        return super(RecentlyModified, self).__call__()

    def update(self):
        brains = self.query_catalog()
        self.batched_results = self.batch(brains)

    def query_catalog(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        query = {
            'sort_on': 'modified',
            'sort_order': 'reverse',
            'path': '/'.join(self.context.getPhysicalPath())}

        return catalog(query)

    def batch(self, brains):
        b_start = self.request.get('b_start', 0)
        return Batch(brains, 20, start=int(b_start))
