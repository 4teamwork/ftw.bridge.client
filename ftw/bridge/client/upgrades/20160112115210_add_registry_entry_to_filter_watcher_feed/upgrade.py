from ftw.upgrade import UpgradeStep


class AddRegistryEntryToFilterWatcherFeed(UpgradeStep):
    """Add registry entry to filter watcher feed.
    """

    def __call__(self):
        self.install_upgrade_profile()
