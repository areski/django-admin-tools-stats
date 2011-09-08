from setuptools import setup
import os
import sys
import re
from django_admin_tools_stats import VERSION


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files, temp_data_files, addons_data_files = [], [], [], []
docs_data_files, resources_data_files = [], []

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


install_flag=False
if sys.argv[1] == "install":
    install_flag = True

setup(
    name='django-admin-tools-stats',
    version=VERSION.replace(' ', '-'),
    description='django-admin-tools-stats is a django application which power dashboard modules with customer stats and charts',
    author='Belaid Arezqui',
    author_email='areski@gmail.com',
    url='http://github.com/Star2Billing/django-admin-tools-stats',
    packages=['django-admin-tools-stats/django_admin_tools_stats/admin_tools_stats',
              'django_admin_tools_stats/docs/',],
    include_package_data=True,
    zip_safe = False,
    install_requires = parse_requirements('django_admin_tools_stats/requirements.txt'),
    dependency_links = parse_dependency_links('django_admin_tools_stats/requirements.txt',
                                              install_flag),
)
