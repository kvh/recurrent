from setuptools import setup, find_packages

version = '0.1.2'

setup(name='recurrent',
      version=version,
      description="Natural language parsing of recurring events",
      long_description=open("README.md").read(),
      classifiers=[
          'Natural Language :: English',
          'Topic :: Text Processing :: Linguistic',
          'License :: OSI Approved :: BSD License'
      ],
      keywords='calendar recurring date event NLP',
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
