from setuptools import setup
import os
import codecs
import sys
import re
import admin_tools_stats


version = admin_tools_stats.__version__


def read(*parts):
    return codecs.open(os.path.join(os.path.dirname(__file__), *parts)).read()


root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)


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


def parse_dependency_links(file_name, install_flag=False):
    dependency_links = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'\s*-e\s+', line):
            dependency_links.append(re.sub(r'\s*-e\s+', '', line))
        if re.match(r'(\s*git)|(\s*hg)', line):
            if install_flag == True:
                line_arr = line.split('/')
                line_arr_length = len(line.split('/'))
                pck_name = line_arr[line_arr_length - 1].split('.git')
                if len(pck_name) == 2:
                    os.system('pip install -f %s %s' % (pck_name[0], line))
                if len(pck_name) == 1:
                    os.system('pip install -f %s %s' % (pck_name, line))
    return dependency_links


# taken from django-registration
# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('admin_tools_stats'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'):
            del dirnames[i]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        prefix = dirpath[len('admin_tools_stats/'):]
                             # Strip "admin_tools_stats/"
        for f in filenames:
            data_files.append(os.path.join(prefix, f))


install_flag = False
if sys.argv[1] == "install":
    install_flag = True

setup(
    name='django-admin-tools-stats',
    version=version,
    description='django-admin-tools-stats is a django application which powers dashboard modules with customer stats and charts',
    long_description=read('README.rst'),
    author='Belaid Arezqui',
    author_email='areski@gmail.com',
    url='http://github.com/Star2Billing/django-admin-tools-stats',
    include_package_data=True,
    zip_safe=False,
    package_dir={'admin_tools_stats': 'admin_tools_stats'},
    packages=packages,
    package_data={'admin_tools_stats': data_files},
    install_requires=parse_requirements(
        'admin_tools_stats/requirements.txt'),
    dependency_links=parse_dependency_links(
        'admin_tools_stats/requirements.txt',
        install_flag),
    license='MIT License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
