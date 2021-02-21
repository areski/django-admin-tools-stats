#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

import base64
import inspect
import unittest

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.test.client import RequestFactory


def build_test_suite_from(test_cases):
    """Returns a single or group of unittest test suite(s) that's ready to be
    run. The function expects a list of classes that are subclasses of
    TestCase.

    The function will search the module where each class resides and
    build a test suite from that class and all subclasses of it.
    """
    test_suites = []
    for test_case in test_cases:
        mod = __import__(test_case.__module__)
        components = test_case.__module__.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        tests = []
        for item in mod.__dict__.values():
            if type(item) is type and issubclass(item, test_case):
                tests.append(item)
        test_suites.append(
            unittest.TestSuite(
                map(unittest.TestLoader().loadTestsFromTestCase, tests),
            ),
        )

    return unittest.TestSuite(test_suites)


class BaseAuthenticatedClient(TestCase):
    """Common Authentication"""
    fixtures = ['auth_user']

    def setUp(self):
        """To create admin user"""
        self.client = Client()
        self.user = User.objects.get(username='admin')
        auth = '%s:%s' % ('admin', 'admin')
        auth = 'Basic %s' % base64.encodestring(auth.encode('utf8'))
        auth = auth.strip()
        self.extra = {
            'HTTP_AUTHORIZATION': auth,
        }
        try:
            self.client.force_login(self.user)
        except AttributeError:  # Django < 1.8
            login = self.client.login(username='admin', password='admin')
            self.assertTrue(login)

        self.factory = RequestFactory()


def assertContainsAny(
        self, response, texts, status_code=200,
        msg_prefix='', html=False,
):
    total_count = 0
    for text in texts:
        text_repr, real_count, msg_prefix = self._assert_contains(response, text, status_code, msg_prefix, html)
        total_count += real_count

    self.assertTrue(total_count != 0, f"None of the {texts} were found in the response: {response}")


class Choice(object):

    class __metaclass__(type):
        def __init__(self, *args, **kwargs):
            self._data = []
            for name, value in inspect.getmembers(self):
                if not name.startswith('_') and not inspect.ismethod(value):
                    if isinstance(value, tuple) and len(value) > 1:
                        data = value
                    else:
                        pieces = [x.capitalize() for x in name.split('_')]
                        data = (value, ' '.join(pieces))
                    self._data.append(data)
                    setattr(self, name, data[0])

            self._hash = dict(self._data)

        def __iter__(self):
            for value, data in self._data:
                yield value, data

        @classmethod
        def get_value(self, key):
            return self._hash[key]
