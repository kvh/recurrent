from setuptools import setup, find_packages

version = '0.2.4'

setup(name='recurrent',
      version=version,
      description="Natural language parsing of recurring events",
      long_description="See http://github.com/kvh/recurrent",
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
      zip_safe=False,
      install_requires=[
          'parsedatetime',
      ]
      )
