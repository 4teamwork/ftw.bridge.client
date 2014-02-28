from setuptools import setup, find_packages
import os

version = '1.0.8'
maintainer = 'Jonas Baumann'

tests_require = [
    'unittest2',
    'mocker',
    'plone.testing',
    'plone.mocktestcase',
    'plone.app.testing',
    'ftw.testing',
    'ftw.builder',

    'transaction',
    'zope.browser',
    'plone.uuid',
    'z3c.autoinclude',  # TODO: eliminate autoinclude in tests
    ]

extras_require = {
    'tests': tests_require,
    'tabbedview': [
        'ftw.tabbedview>=3.2.3',
        'ftw.table']}

tests_require += extras_require['tabbedview']


setup(name='ftw.bridge.client',
      version=version,
      description='Adds ftw.bridge support to plone.',

      long_description=open('README.rst').read() + '\n' + \
          open(os.path.join('docs', 'HISTORY.txt')).read(),

      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        'Framework :: Plone',
        'Framework :: Plone :: 4.1',
        'Framework :: Plone :: 4.2',
        'Framework :: Plone :: 4.3',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        ],

      keywords='ftw bridge proxy client',
      author='4teamwork GmbH',
      author_email='mailto:info@4teamwork.ch',
      maintainer=maintainer,
      url='https://github.com/4teamwork/ftw.bridge.client',
      license='GPL2',

      packages=find_packages(),
      namespace_packages=['ftw', 'ftw.bridge'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
          'setuptools',

          # Zope
          'AccessControl',
          'Acquisition',
          'Missing',
          'zope.component',
          'zope.app.component',
          'zope.formlib',
          'zope.i18nmessageid',
          'zope.interface',
          'zope.publisher',
          'zope.schema',
          'Zope2',

          # Plone
          'Products.statusmessages',
          'plone.memoize',
          'plone.portlets',
          'plone.app.portlets',
          'Products.GenericSetup',
          'Products.PluggableAuthService',
          'Products.CMFCore',
          'Products.CMFPlone',
      ],

      tests_require=tests_require,
      extras_require=extras_require,

      entry_points='''
      [z3c.autoinclude.plugin]
      target = plone
      ''',
      )
