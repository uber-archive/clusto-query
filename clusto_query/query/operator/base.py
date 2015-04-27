# Copyright (c) 2013-2015, Uber, Inc.
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import clusto_query


class OperatorType(clusto_query.query.QueryType):
    def __new__(mcs, cls, *args, **kwargs):
        constructed_class = super(OperatorType, mcs).__new__(mcs, cls, *args, **kwargs)
        if getattr(constructed_class, "operator_map", None) is not None and \
                getattr(constructed_class, "operator", None) is not None:
            if isinstance(constructed_class.operator, basestring):
                constructed_class.operator_map[constructed_class.operator] = constructed_class
            else:
                for operator in constructed_class.operator:
                    constructed_class.operator_map[operator] = constructed_class
        return constructed_class


class Operator(clusto_query.query.QueryObject):
    __metaclass__ = OperatorType

    def __init__(self, *parameters):
        self.parameters = parameters

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ", ".join(map(repr, self.parameters)))

    def visit_iter(self):
        yield self
        for param in self.parameters:
            if isinstance(param, clusto_query.query.QueryObject):
                for p in param.visit_iter():
                    yield p
            else:
                yield param
