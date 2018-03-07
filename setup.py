from setuptools import setup
setup(
  name = 'aqualogic',
  packages = ['aqualogic'], # this must be the same as the name above
  version = '0.1',
  description = 'Library for interfacing with a Hayward/Goldline AquaLogic/ProLogic pool controller.',
  author = 'Sean Wilson',
  author_email = 'sean.wilson@live.ca',
  url = 'https://github.com/swilson/aqualogic',
  download_url = 'https://github.com/swilson/aqualogic/archive/0.1.tar.gz',
  license='MIT',
  classifiers=[
      # How mature is this project? Common values are
      #   3 - Alpha
      #   4 - Beta
      #   5 - Production/Stable
      'Development Status :: 4 - Beta',

      # Indicate who your project is intended for
      'Intended Audience :: Developers',
      'Topic :: Software Development :: Embedded Systems',

      'License :: OSI Approved :: MIT License',

      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.2',
      'Programming Language :: Python :: 3.3',
      'Programming Language :: Python :: 3.4',
  ],
  install_requires=['zope.event>=4.3']
)
