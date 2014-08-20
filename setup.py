from setuptools import setup, find_packages
import os

version = '1.0.9'

tests_require = [
    'ftw.builder',
    'ftw.testing',
    'mocker',
    'plone.app.testing',
    'plone.mocktestcase',
    'plone.testing',
    'plone.uuid',
    'transaction',
    'unittest2',
    'z3c.autoinclude',  # TODO: eliminate autoinclude in tests
    'zope.browser',
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
      author='4teamwork AG',
      author_email='mailto:info@4teamwork.ch',
      url='https://github.com/4teamwork/ftw.bridge.client',
      license='GPL2',

      packages=find_packages(),
      namespace_packages=['ftw', 'ftw.bridge'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
          'AccessControl',
          'Acquisition',
          'Missing',
          'Products.CMFCore',
          'Products.CMFPlone',
          'Products.GenericSetup',
          'Products.PluggableAuthService',
          'Products.statusmessages',
          'Zope2',
          'plone.app.portlets',
          'plone.memoize',
          'plone.portlets',
          'setuptools',
          'zope.app.component',
          'zope.component',
          'zope.formlib',
          'zope.i18nmessageid',
          'zope.interface',
          'zope.publisher',
          'zope.schema',
      ],

      tests_require=tests_require,
      extras_require=extras_require,

      entry_points='''
      [z3c.autoinclude.plugin]
      target = plone
      ''',
      )
