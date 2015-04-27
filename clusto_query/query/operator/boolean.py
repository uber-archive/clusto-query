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

from clusto_query.query.operator.base import Operator
from clusto_query import optimizer


BOOLEAN_OPERATORS = {}
UNARY_BOOLEAN_OPERATORS = {}


class BooleanOperator(Operator):
    operator_map = BOOLEAN_OPERATORS


class Intersection(BooleanOperator):
    operator = ("&", "and")

    def run(self, candidate_hosts, context):
        results = set(candidate_hosts)
        for p in optimizer.sort_clauses(self.parameters):
            results &= p.run(results, context)
        return results


class Union(BooleanOperator):
    operator = ("|", "or")

    def run(self, candidate_hosts, context):
        results = set()
        for p in self.parameters:
            results |= p.run(candidate_hosts, context)
        return results


class Subtraction(BooleanOperator):
    operator = "-"

    def run(self, candidate_hosts, context):
        results = self.parameters[0].run(candidate_hosts, context)
        for p in self.parameters[1:]:
            results -= p.run(candidate_hosts, context)
        return results


class UnaryBooleanOperator(Operator):
    operator_map = UNARY_BOOLEAN_OPERATORS


class Not(UnaryBooleanOperator):
    operator = ("not", "~")

    def run(self, candidate_hosts, context):
        return set(candidate_hosts) - self.parameters[0].run(candidate_hosts, context)
