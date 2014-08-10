import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

link = 'git+https://github.com/prathamesh920/\
django-taggit-autocomplete-modified.git'

setup(
    name='django-exam',
    author='Prabhu Ramachandran',
    author_email='prabhu.ramachandran@gmail.com',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',
    entry_points = {
            'console_scripts': [
                'code_server = exam.code_server:main',
            ],
    },
    description='A django app to conduct online test.',
    long_description=README,
    install_requires=[
        'django',
        'django-taggit',
        'django-taggit-autocomplete-modified>=0.2',
    ],
    dependency_links=[link+'#egg=django_taggit_autocomplete_modified-0.2'],
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
