from Acquisition import aq_inner
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from ftw.bridge.client import _
from plone.app.portlets.portlets import base
from plone.memoize.compress import xhtml_compress
from plone.portlets.interfaces import IPortletDataProvider
from zope import schema
from zope.component import getMultiAdapter
from zope.formlib import form
from zope.interface import implements


class IWatcherPortlet(IPortletDataProvider):

    # Remote client to call through the bridge for receiving the recently
    # modified feed.
    client_id = schema.TextLine(
        title=u'Client ID',
        required=True)

    # Path and view to call on the remote client.
    path = schema.TextLine(
        title=u'Path',
        required=True)


class Assignment(base.Assignment):

    implements(IWatcherPortlet)

    def __init__(self, client_id, path):
        self.client_id = client_id
        self.path = path

    @property
    def title(self):
        return _(u'title_watcher_portlet',
                 default='Recently modified')


class Renderer(base.Renderer):

    _template = ViewPageTemplateFile('templates/watcher.pt')

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)

        context = aq_inner(self.context)
        portal_state = getMultiAdapter(
            (context, self.request),
            name=u'plone_portal_state')
        self.anonymous = portal_state.anonymous()

    @property
    def available(self):
        return not self.anonymous

    @property
    def title(self):
        return _(u'title_watcher_portlet',
                 default='Recently modified')

    def render(self):
        return xhtml_compress(self._template())


class AddForm(base.AddForm):

    form_fields = form.Fields(IWatcherPortlet)
    label = _(u'title_watcher_portlet',
              default='Recently modified')

    def create(self, data):
        return Assignment(**data)
