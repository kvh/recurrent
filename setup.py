from setuptools import setup, find_packages

version = '0.1'

setup(name='recurrent',
      version=version,
      description="Natural language parsing of recurring events",
      long_description=open("README.md").read(),
      classifiers=[
      ],
      keywords='calendar recurring date event',
      author='Ken Van Haren',
      author_email='kvh@science.io',
      url='http://github.com/kvh/recurrent',
      license='BSD',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'parsedatetime',
      ]
      )
