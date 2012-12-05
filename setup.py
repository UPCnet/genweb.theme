from setuptools import setup, find_packages
import os

version = '1.0b1'

setup(name='genweb.theme',
      version=version,
      description="Theme package for GenwebUPC.",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='theme genweb plone',
      author='UPCnet Plone Team',
      author_email='plone.team@upcnet.es',
      url='https://github.com/UPCnet/genweb.theme.git',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['genweb'],
      extras_require={'test': ['plone.app.testing',
                               'robotsuite',
                               'robotframework-selenium2library']},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'five.grok',
          'z3c.jbot',
          'genweb.core',
          'genweb.controlpanel',
          'pyScss',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
