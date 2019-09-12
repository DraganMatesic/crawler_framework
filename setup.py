from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='crawler_framework',
      version='0.1.7',
      description='Framework for crawling',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Dragan Matesic',
      author_email='dragan.matesic@gmail.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False,
      install_requires=['SQLAlchemy', 'pandas', 'requests', 'bs4', 'stem', 'pymssql', 'pyodbc', 'stem', 'psycopg2', 'cx_oracle',
                        'aiohttp_socks', 'aiohttp', 'psutil', 'virtualenv', 'lxml', 'virtualenv'],
      scripts=['scripts/config.py', 'scripts/configv3.py']
      )
