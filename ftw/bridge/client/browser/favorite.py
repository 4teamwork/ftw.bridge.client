from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView


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
