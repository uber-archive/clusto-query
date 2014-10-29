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
