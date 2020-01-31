import os
import re

from setuptools import find_packages, setup

import admin_tools_stats


def runtests(*args, **kwargs):
    import os
    import sys

    import django
    from django.core.management import call_command

    os.environ['DJANGO_SETTINGS_MODULE'] = 'demoproject.test_settings'
    django.setup()
    call_command('test', 'admin_tools_stats')
    sys.exit()


def read(*parts):
    return open(os.path.join(os.path.dirname(__file__), *parts)).read()


def parse_requirements(file_name):
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        if re.match(r'\s*-e\s+', line):
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
        elif re.match(r'(\s*git)|(\s*hg)', line):
            pass
        else:
            requirements.append(line)
    return requirements


def parse_dependency_links(file_name):
    dependency_links = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'\s*-[ef]\s+', line):
            dependency_links.append(re.sub(r'\s*-[ef]\s+', '', line))

    return dependency_links


setup(
    name='django-admin-charts',
    version=admin_tools_stats.__version__,
    description='django-admin-charts - Easily configurable charts statistics for `django-admin` and `django-admin-tools`',
    long_description=read('README.rst'),
    author='Petr Dlouhy',
    author_email='petr.dlouhy@email.cz',
    url='https://github.com/PetrDlouhy/django-admin-charts',
    include_package_data=True,
    zip_safe=False,
    package_dir={'admin_tools_stats': 'admin_tools_stats'},
    packages=find_packages(),
    package_data={},
    install_requires=parse_requirements('requirements.txt'),
    dependency_links=parse_dependency_links('requirements.txt'),
    license='MIT License',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    extras_require={
        ':python_version >= "3.0"': ['Django>=2.0'],
    },
    test_suite='setup.runtests',
)
