#!/usr/bin/env python

from setuptools import setup

def readme():
    with open('readme.md') as f:
        return f.read()

setup(
    name='ansible_hint',
    version='0.0',
    description='Configurable linter for Ansible',
    long_description=readme(),
    url='http://nowhere.nowhere',
    author='Eric Anderton',
    author_email='eric.t.anderton@gmail.com',
    license='MIT',
    packages=['ansible_hint'],
    scripts=[
        'bin/ansible_hint'
    ],
    install_requires=[
        'simpleparse'
    ],
    test_suite='nose.collector',
    tests_require=[
        'nose'
    ],
    #include_package_data=True,  # NOTE: enable for MANIFEST.in data to install into site-packages
    zip_safe=False)
