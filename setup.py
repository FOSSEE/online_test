import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='yaksh',
    author='Python Team at FOSSEE, IIT Bombay',
    author_email='python@fossee.in',
    version='0.1.1',
    packages=find_packages(),
    include_package_data=True,
    url = 'https://pypi.python.org/pypi/yaksh/',
    license='BSD License',
    entry_points = {
            'console_scripts': [
                'yaksh = yaksh.scripts.cli:main',
            ],
    },
    description='A django app to conduct online tests.',
    long_description=README,
    install_requires=[
        'django==1.9.5',
        'mysql-python==1.2.5',
        'django-taggit==0.18.1',
        'pytz==2016.4',
        'python-social-auth==0.2.19'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
