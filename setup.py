from setuptools import setup
setup(
  name = 'aqualogic',
  packages = ['aqualogic'], # this must be the same as the name above
  version = '3.3',
  description = 'Library for interfacing with a Hayward/Goldline AquaLogic/ProLogic pool controller.',
  long_description = 'A python library to interface with Hayward/Goldline AquaLogic/ProLogic pool controllers. Note that the Goldline protocol uses RS-485 so a hardware interface that can provide the library with reader and writer file objects is required. The simplest solution for this is an RS-485 to Ethernet adapter connected via a socket.',
  author = 'Sean Wilson',
  author_email = 'sean.wilson@live.ca',
  url = 'https://github.com/swilson/aqualogic',
  license='MIT',
  classifiers=[
      # How mature is this project? Common values are
      #   3 - Alpha
      #   4 - Beta
      #   5 - Production/Stable
      'Development Status :: 5 - Production/Stable',

      # Indicate who your project is intended for
      'Intended Audience :: Developers',
      'Topic :: Software Development :: Embedded Systems',

      'License :: OSI Approved :: MIT License',

      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.2',
      'Programming Language :: Python :: 3.3',
      'Programming Language :: Python :: 3.4',
  ],
  install_requires=[
    'pyserial',
    'websockets',
  ],
  include_package_data = True
)
