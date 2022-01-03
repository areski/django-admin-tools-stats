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

import inspect


class Choice(object):
    class __metaclass__(type):
        def __init__(cls, *args, **kwargs):
            cls._data = []
            for name, value in inspect.getmembers(cls):
                if not name.startswith("_") and not inspect.ismethod(value):
                    if isinstance(value, tuple) and len(value) > 1:
                        data = value
                    else:
                        pieces = [x.capitalize() for x in name.split("_")]
                        data = (value, " ".join(pieces))
                    cls._data.append(data)
                    setattr(cls, name, data[0])

            cls._hash = dict(cls._data)

        def __iter__(cls):
            for value, data in cls._data:
                yield value, data

        @classmethod
        def get_value(cls, key):
            return cls._hash[key]
