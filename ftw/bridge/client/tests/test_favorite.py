from Products.CMFCore.utils import getToolByName
from ftw.bridge.client.testing import INTEGRATION_TESTING
from plone.mocktestcase.dummy import Dummy
from unittest2 import TestCase


class TestAddWatcherPortletView(TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.mtool = getToolByName(self.portal, 'portal_membership')
        self.folder = self.mtool.getHomeFolder()

    def tearDown(self):
        if 'title' in self.request.form:
            del self.request.form['title']

        if 'url' in self.request.form:
            del self.request.form['url']

        if 'Favorites' in self.folder.objectIds():
            self.folder.manage_delObjects(['Favorites'])

    def test_component_is_registered(self):
        self.portal.restrictedTraverse('@@add-favorite')

    def test_get_favorites_folder(self):
        self.assertNotIn('Favorites', self.folder.objectIds())
        view = self.portal.restrictedTraverse('@@add-favorite')
        folder = view.get_favorites_folder()
        self.assertNotEquals(folder, None)
        self.assertIn('Favorites', self.folder.objectIds())

    def test_adds_link_object(self):
        self.assertNotIn('Favorites', self.folder.objectIds())
        view = self.portal.restrictedTraverse('@@add-favorite')

        self.request.form['title'] = 'Google search'
        self.request.form['url'] = 'http://www.google.com/'

        self.assertEquals(view(), 'OK')
        folder = view.get_favorites_folder()
        self.assertEquals(len(folder.objectValues()), 1)
        link = folder.objectValues()[0]
        self.assertEquals(link.Title(), 'Google search')
        self.assertEquals(link.getRemoteUrl(), 'http://www.google.com/')

    def test_generate_favorite_id(self):
        mock_folder = Dummy(objectIds=lambda: ['favorite-1', 'favorite-2'])
        view = self.portal.restrictedTraverse('@@add-favorite')
        self.assertEqual(view.generate_favorite_id(mock_folder),
                         'favorite-3')
