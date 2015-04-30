#!/usr/bin/env python
"""
sentry-slack-webhooks
=====================

An extension for Sentry which allows to push events to the slack incoming webhooks.

Project forked from the generic sentry-webhooks plugin.

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from setuptools import setup, find_packages


tests_require = [
    'nose',
]

install_requires = [
    'ipaddr',
    'sentry>=5.0.0',
]

setup(
    name='sentry-slack-webhooks',
    version='0.2.0',
    author='Massimiliano Torromeo',
    author_email='massimiliano.torromeo@gmail.com',
    url='http://github.com/mtorromeo/sentry-slack-webhooks',
    description='A Sentry extension which pushes events to the slack incoming webhooks.',
    long_description=__doc__,
    license='BSD',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    test_suite='runtests.runtests',
    include_package_data=True,
    entry_points={
       'sentry.apps': [
            'webhooks = sentry_slack_webhooks',
        ],
       'sentry.plugins': [
            'webhooks = sentry_slack_webhooks.plugin:SlackWebHooksPlugin'
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
