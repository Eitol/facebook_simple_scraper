from setuptools import setup, find_packages

setup(
    name='facebook_simple_scraper',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pydantic~=2.7.1',
        'requests~=2.31.0',
        'beautifulsoup4~=4.12.3',
        'python-dateutil~=2.9.0.post0',
        'dateparser~=1.2.0',
    ],
    author='Hector Oliveros',
    author_email='hector.oliveros.leon@gmail.com',
    description='A simple scraper for Facebook',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Eitol/facebook_simple_scraper',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.12',
)
