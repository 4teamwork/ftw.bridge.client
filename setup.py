from setuptools import setup, find_packages
import os

version = '1.0.1'
maintainer = 'Jonas Baumann'

tests_require = [
    'plone.app.testing',
    'ftw.testing',
    'ftw.tabbedview',
    ]

extras_require = {
    'tests': tests_require,
    'tabbedview': ['ftw.tabbedview']}


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
          'Products.PluggableAuthService',
      ],
      tests_require=tests_require,
      extras_require=extras_require,

      entry_points='''
      [z3c.autoinclude.plugin]
      target = plone
      ''',
      )
