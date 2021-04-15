import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


def get_version():
    import os
    data = {}
    fname = os.path.join('online_test', '__init__.py')
    exec(compile(open(fname).read(), fname, 'exec'), data)
    return data.get('__version__')


install_requires = [
    'django==3.1.7',
    'django-taggit==1.2.0',
    'pytz==2019.3',
    'requests-oauthlib>=0.6.1',
    'python-social-auth==0.2.19',
    'tornado',
    'psutil',
    'ruamel.yaml==0.15.23',
    'invoke==0.21.0',
    'requests',
    'markdown==2.6.9',
]

setup(
    name='yaksh',
    author='Python Team at FOSSEE, IIT Bombay',
    author_email='python@fossee.in',
    version=get_version(),
    packages=find_packages(),
    include_package_data=True,
    url='https://pypi.python.org/pypi/yaksh/',
    license='BSD License',
    entry_points={
            'console_scripts': [
                'yaksh = yaksh.code_server:main',
            ],
    },
    description='A django app to conduct online programming tests.',
    long_description=README,
    install_requires=install_requires,
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
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
