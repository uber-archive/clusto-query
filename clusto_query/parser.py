import re

from clusto_query.exceptions import (StringParseError,
                                     ExpectedTokenError,
                                     UnexpectedTokenError)
from clusto_query.query.objects import Attribute
from clusto_query.query.operator import (UNARY_BOOLEAN_OPERATORS,
                                         SUFFIX_OPERATORS,
                                         INFIX_OPERATORS,
                                         BOOLEAN_OPERATORS)


_attribute_re = re.compile(r'([\w-]+)(\.([\w-]+))?(\:([0-9]+))?')


def _expect(token, q):
    if not q or q[0] != token:
        raise ExpectedTokenError(token, q[0])
    else:
        return q[1:]


def parse_attribute(q):
    smd = _attribute_re.match(q[0])
    if not smd:
        raise StringParseError
    return Attribute(smd.group(1), smd.group(3), smd.group(5)), q[1:]


def parse_expression(q):
    if q[0] == "(":
        lhs, q = parse_boolean(q[1:])
        q = _expect(")", q)
        return lhs, q
    elif q[0] == "attr":
        lhs, q = parse_attribute(_expect("attr", q))
    elif "." in q[0]:
        raise StringParseError("Found a . in %s; missing attr?" % q[0])
    else:
        for op, kls in sorted(UNARY_BOOLEAN_OPERATORS.iteritems(), key=len, reverse=True):
            if op == q[0]:
                exp, rest = parse_expression(_expect(op, q))
                return kls(exp), rest
        else:
            lhs = q[0]
            q = q[1:]
    for op, kls in sorted(SUFFIX_OPERATORS.iteritems(), key=len, reverse=True):
        if q[0] == op:
            return kls(lhs), q[1:]
    for op, kls in sorted(INFIX_OPERATORS.iteritems(), key=len, reverse=True):
        if q[0] == op:
            return kls(lhs, q[1]), q[2:]
    else:
        raise UnexpectedTokenError(q)


def parse_boolean(q):
    lhs, rest = parse_expression(q)
    if rest:
        for op, kls in sorted(BOOLEAN_OPERATORS.iteritems(), key=len, reverse=True):
            if rest[0] == op:
                rhs, rest = parse_boolean(rest[1:])
                lhs = kls(lhs, rhs)
                break
        else:
            if rest[0] == ")":
                return lhs, rest
            else:
                raise UnexpectedTokenError(rest)
    return lhs, rest


def parse_query(q):
    return parse_boolean(q)
