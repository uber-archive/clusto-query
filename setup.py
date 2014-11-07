from setuptools import setup, find_packages


setup(name='clusto_query',
      version='0.4.7',
      author='James Brown',
      author_email='jbrown@uber.com',
      description='Perform arbitrary boolean queries against clusto',
      install_requires=map(str.strip, open('requirements.txt').readlines()),
      packages=find_packages(exclude='test'),
      entry_points={
          'console_scripts': [
              'clusto-query = clusto_query.scripts.main:main',
          ]})
