from ftw.bridge.client.testing import EXAMPLE_CONTENT_LAYER
from unittest2 import TestCase
import os.path


class TestRecentlyModifiedView(TestCase):

    layer = EXAMPLE_CONTENT_LAYER

    def setUp(self):
        self.folder = self.layer['portal'].get('feed-folder')
        self.layer['request'].ACTUAL_URL = os.path.join(
            self.folder.absolute_url(),
            '@@watcher-recently-modified')

    def test_batched_results(self):
        view = self.folder.restrictedTraverse('@@watcher-recently-modified')
        view.update()
        result = view.batched_results

        self.assertNotEqual(result, None)
        self.assertEqual(result.__class__.__name__, 'Batch')
        self.assertEqual(len(result), 2)

        # do not expect a order since the folder and the page are
        # created at the same time - it may switch in some cases.
        brain_ids = [brain.id for brain in result]
        self.assertEqual(set(brain_ids), set(['feed-folder', 'page']))

    def test_template_renders(self):
        view = self.folder.restrictedTraverse('@@watcher-recently-modified')
        html = view()

        self.assertIn(u'The page with uml\xe4uts', html)
        self.assertIn(u'Feed folder', html)
