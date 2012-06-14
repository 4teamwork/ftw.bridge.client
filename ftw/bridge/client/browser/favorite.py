from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from ftw.bridge.client import _
from ftw.bridge.client.exceptions import MaintenanceError
from ftw.bridge.client.interfaces import IBridgeRequest
from ftw.bridge.client.interfaces import MAINTENANCE_ERROR_MESSAGE
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
from zope.component import getMultiAdapter
from zope.component import getUtility


class AddFavorite(BrowserView):
    """This view adds a Link object to the "Favorites" folder located in
    the home folder of the current member. The Link has `title` and is
    pointing to the `url` passed in as request data.
    The view is meant to be called on the site hosting the dashboard and
    can be called by the bridge proxy.
    """

    def __call__(self):
        url = self.request.form['url']
        title = self.request.form['title']

        folder = self.get_favorites_folder()
        id_ = self.generate_favorite_id(folder)
        folder.invokeFactory('Link', id=id_, title=title, remoteUrl=url)

        return 'OK'

    def get_favorites_folder(self):
        membership = getToolByName(self.context, 'portal_membership')
        folder = membership.getHomeFolder()
        if 'Favorites' not in folder.objectIds():
            folder.invokeFactory('Folder', 'Favorites', title='Favorites')
        return folder.get('Favorites')

    def generate_favorite_id(self, favorites_folder, base='favorite'):
        existing_ids = favorites_folder.objectIds()

        idx = 1
        while True:
            id_ = '%s-%d' % (base, idx)
            if id_ not in existing_ids:
                return id_
            idx += 1


class RemoteAddFavoriteAction(BrowserView):
    """This view adds a favorite (Link object) on the remote site called
    "dashboard" over the bridge proxy. The link object points to the current
    context.
    """

    def __call__(self):
        self._create_favorite(title=self.context.Title(),
                              url=self._get_url())

        referer = self.request.environ.get('HTTP_REFERER')
        if referer:
            self.request.RESPONSE.redirect(referer)
        else:
            state = getMultiAdapter((self.context, self.request),
                                    name='plone_context_state')
            self.request.RESPONSE.redirect(state.view_url())

    def _create_favorite(self, title, url):
        data = {'title': title,
                'url': url}

        requester = getUtility(IBridgeRequest)
        try:
            response = requester('dashboard', '@@add-favorite',
                                 data=data, silent=True)

        except MaintenanceError:
            IStatusMessage(self.request).addStatusMessage(
                MAINTENANCE_ERROR_MESSAGE, type='error')
            return False

        if response is None or response.code != 200:
            IStatusMessage(self.request).addStatusMessage(
                _(u'favorite_creation_failed',
                  default=u'The favorite could not be created.'),
                type='error')
            return False

        else:
            IStatusMessage(self.request).addStatusMessage(
                _(u'info_favorite_created',
                  default=u'${title} was added to your favorites.',
                  mapping={'title': title.decode('utf-8')}),
                type='info')
            return True

    def _get_url(self):
        state = getMultiAdapter((self.context, self.request),
                                name='plone_context_state')

        portal_url = getToolByName(self.context, 'portal_url')() + '/'
        relative_path = state.view_url()[len(portal_url):]
        return ''.join((PORTAL_URL_PLACEHOLDER, relative_path))
