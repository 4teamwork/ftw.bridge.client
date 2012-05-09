Introduction
============

The ``ftw.bridge`` tools are used for communication between several Plone
instances.
It is also possible to cummuncate with other web services.
Requests between web services are proxied through the `ftw.bridge.proxy`_.
This makes it possible to move or reconfigure certain dependent webservices
(clients) only by reconfiguring the proxy.
The clients do not know where other target clients are located - they only
communicate with the proxy directly, which forwards the requests to the
target client.


Features
--------

``ftw.bridge.client`` integrates ``ftw.bridge`` support into Plone.
It provides tools and utilities for communication and authentication.

- **Authentication**: A PAS plugin authenticates requests and logs the user
  in on the target client without transmitting his password. Only requests
  from the configured `ftw.bridge.proxy`_ are authenticated.

- **Requests**: The ``IBridgeRequest`` utility is used for making requesting
  other clients. It is also able to make remote catalog queries and
  transmitting the result brains to the sources by using fake brains.

- **Brain transport**: By using a ``BrainRepresentation`` it is possible to
  get brains from a remote client. A ``BrainSerializer`` utility serializes
  and deserializes all brain metadata so that they can be used on the source
  client.

- **Watcher portlet**: A recently-modified portlet can be used for generic
  listing a list of recently modified objects on the remote client but it
  is also possible to list other links. There is a browser view ``@@watch``
  which creates a recently-modified portlet on the remote client
  ``dashboard``. The watcher portlet loads its data asynchronously using
  javascript for not blocking while loading the dashboard.

- **Favorites**: A browser view ``@@remote-add-favorite`` adds the context
  to the favorites on the remote client ``dashboard``.


Installation and configuration
------------------------------

- A installation of `ftw.bridge.proxy`_ is required.

- Add ``ftw.bridge.client`` to your eggs in the buildout configuration::

    [instance]
    eggs +=
        ftw.bridge.client

- Configure the `ftw.bridge.proxy`_ data as environment variables::

    [instance]
    environment-vars +=
        bridge_url http://localhost:1234/proxy
        bridge_ips 127.0.0.1, 192.168.1.10
        bridge_client_id workspace

- Install the generic setup profile. This registers the portlet and installs
  a PAS plugin.


Configuration Options
---------------------

The configuration options are set using environment variables:

- ``bridge_url``: The url to the "/proxy" view of `ftw.bridge.proxy`_.
- ``bridge_ips``: A comma seperated list of trusted IPs of the
  `ftw.bridge.proxy`_ installation.
- ``bridge_client_id``: The id of this client as configured in the ``.ini``
  file on ``ftw.bridge.proxy``.


Links
-----

- Github project repository: https://github.com/4teamwork/ftw.bridge.proxy
- Issue tracker: https://github.com/4teamwork/ftw.bridge.proxy/issues
- Package on pypi: http://pypi.python.org/pypi/ftw.bridge.proxy
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.bridge.proxy


Copyright
---------

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.bridge.client`` is licensed under GNU General Public License, version 2.


.. _ftw.bridge.proxy: https://github.com/4teamwork/ftw.bridge.proxy
