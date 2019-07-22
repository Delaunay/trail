#!/usr/bin/env python

from setuptools import setup


if __name__ == '__main__':
    setup(
        name='track',
        version='0.0.0',
        description='Simple utility to track experiments',
        author='Pierre Delaunay',
        package_data={
            'track': ['distributed/cockroach/*']
        },
        packages=[
            'track',
            'track.aggregators',
            'track.containers',
            'track.persistence',
            'track.utils',
            'track.distributed',
            'track.dashboard'
        ],
        install_requires=[
            'dataclasses',
            'typing'
        ],
        extras_require={
            'cockroack': ['psycopg2-binary'],
            'cometml': ['cometml'],
            'mongo': ['pymongo'],
            'orion': ['orion.core']
        },
        dependency_links=[
            'git+git://github.com/Delaunay/benchutils@master#egg=benchutils',
            'git+git://github.com/Delaunay/orion.git@track'
        ],
        setup_requires=['setuptools'],
        tests_require=['pytest', 'flake8', 'codecov', 'pytest-cov'],
    )
