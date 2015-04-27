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
from clusto_query.query.operator.affix import Equality
from clusto_query.query.objects import Attribute


def score_clause(clause):
    score = 0
    if isinstance(clause, Equality):
        score -= 1
    for possible_key in ('lhs', 'rhs'):
        subclause = getattr(clause, possible_key, None)
        if subclause is None:
            continue
        if isinstance(subclause, Attribute):
            score += 100
        elif isinstance(subclause, Operator):
            score -= 1
    return score


def sort_clauses(iterable):
    sort_space = []

    for item in iterable:
        score = score_clause(item)
        sort_space.append((score, item))

    return [v for (s, v) in sorted(sort_space)]
