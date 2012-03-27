from ftw.testing.layer import ComponentRegistryLayer


class ZCMLLayer(ComponentRegistryLayer):
    """A layer which only sets up the zcml, but does not start a zope
    instance.
    """

    def setUp(self):
        super(ZCMLLayer, self).setUp()

        import ftw.bridge.client.tests
        self.load_zcml_file('tests.zcml', ftw.bridge.client.tests)


ZCML_LAYER = ZCMLLayer()
