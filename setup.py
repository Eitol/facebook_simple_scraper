from setuptools import setup, find_packages


def read_version():
    with open('facebook_simple_scraper/__init__.py') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().replace("'", '').replace('"', '')
    return '0.0.0'


def increment_and_update_version():
    version = read_version()
    major, minor, patch = map(int, version.split('.'))
    patch += 1
    new_version = f"{major}.{minor}.{patch}"

    with open('facebook_simple_scraper/__init__.py', 'r+') as f:
        content = f.read()
        f.seek(0)
        f.truncate()
        f.write(content.replace(version, new_version))

    return new_version.replace("'", '').replace('"', '')


setup(
    name='facebook_simple_scraper',
    version=increment_and_update_version(),
    packages=find_packages(include=['facebook_simple_scraper', 'facebook_simple_scraper.*']),
    include_package_data=True,
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
    license="MIT",
)
