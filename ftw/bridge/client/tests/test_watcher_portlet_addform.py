from ftw.bridge.client.testing import FUNCTIONAL_TESTING
from ftw.bridge.client.tests.base import RequestAwareTestCase
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.testing import setRoles
from plone.testing.z2 import Browser
import os.path
import transaction


class TestWatcherPortletAddForm(RequestAwareTestCase):

    layer = FUNCTIONAL_TESTING

    def setUp(self):
        super(RequestAwareTestCase, self).setUp()
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID,
                 ['Manager', 'Member', 'Site Administrator'])

        transaction.commit()

        self.browser = Browser(self.layer['app'])
        self.browser.handleErrors = False
        self.browser.open('%s/login_form' % self.portal.absolute_url())
        self.browser.getControl(name='__ac_name').value = TEST_USER_NAME
        self.browser.getControl(
            name='__ac_password').value = TEST_USER_PASSWORD
        self.browser.getControl(name='submit').click()
        self.assertIn('You are now logged in', self.browser.contents)

    def tearDown(self):
        super(RequestAwareTestCase, self).tearDown()
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        self.browser.open('%s/logout' % self.portal.absolute_url())
        transaction.commit()

    def test_portlet_addable(self):
        url = os.path.join(self.portal.absolute_url(),
                           '@@manage-portlets')
        self.browser.open(url)
        self.assertNotIn('You do not have sufficient privileges',
                         self.browser.contents)
        self.assertIn('Recently modified', self.browser.contents)

        self.assertEqual(
            self.browser.getControl('Recently modified', index=1).optionValue,
            '/++contextportlets++plone.rightcolumn/+/' +
            'ftw.bridge.client.watcher_portlet')

    def test_portlet_addform(self):
        self.assertEqual(
            self.portal.restrictedTraverse(
                '++contextportlets++plone.rightcolumn').keys(),
            [])

        url = os.path.join(self.portal.absolute_url(),
                           '++contextportlets++plone.rightcolumn',
                           '+/ftw.bridge.client.watcher_portlet')
        self.browser.open(url)

        self.assertNotIn('You do not have sufficient privileges',
                         self.browser.contents)
        self.assertIn('Client ID', self.browser.contents)

        self.browser.getControl('Client ID').value = 'foo'
        self.browser.getControl('Path').value = '@@bar?baz=1'
        self.browser.getControl('Save').click()

        mapping = self.portal.restrictedTraverse(
            '++contextportlets++plone.rightcolumn')
        self.assertEqual(
            mapping.keys(),
            ['title_watcher_portlet'])
        assignment = mapping.get('title_watcher_portlet')
        self.assertEqual(assignment.client_id, u'foo')
        self.assertEqual(assignment.path, u'@@bar?baz=1')
