from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from ftw.bridge.client import _
from ftw.bridge.client.exceptions import MaintenanceError
from ftw.bridge.client.interfaces import IBridgeRequest
from ftw.bridge.client.interfaces import MAINTENANCE_ERROR_MESSAGE
from ftw.bridge.client.interfaces import PORTAL_URL_PLACEHOLDER
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
            self.request.RESPONSE.redirect(self.context.absolute_url())

    def _create_favorite(self, title, url):
        params = {'title': title,
                'url': url}

        requester = getUtility(IBridgeRequest)
        try:
            response = requester('dashboard', '@@add-favorite',
                                 params=params)

        except MaintenanceError:
            IStatusMessage(self.request).addStatusMessage(
                MAINTENANCE_ERROR_MESSAGE, type='error')
            return False

        if response.status_code == 200:
            IStatusMessage(self.request).addStatusMessage(
                _(u'info_favorite_created',
                  default=u'${title} was added to your favorites.',
                  mapping={'title': title}),
                type='info')
            return True

        else:
            IStatusMessage(self.request).addStatusMessage(
                _(u'favorite_creation_failed',
                  default=u'The favorite could not be created.'),
                type='error')
            return False

    def _get_url(self):
        portal_url = getToolByName(self.context, 'portal_url')() + '/'
        relative_path = self.context.absolute_url()[len(portal_url):]
        return ''.join((PORTAL_URL_PLACEHOLDER, relative_path))