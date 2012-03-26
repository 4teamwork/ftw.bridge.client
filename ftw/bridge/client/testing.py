from ftw.testing.layer import ComponentRegistryLayer


class ZCMLLayer(ComponentRegistryLayer):
    """A layer which only sets up the zcml, but does not start a zope
    instance.
    """

    def setUp(self):
        super(ZCMLLayer, self).setUp()
        import ftw.bridge.client
        self.load_zcml_file('configure.zcml', ftw.bridge.client)


ZCML_LAYER = ZCMLLayer()
