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

import re
from clusto_query.exceptions import StringParseError
from clusto_query.query.operator import (BOOLEAN_OPERATORS,
                                         UNARY_BOOLEAN_OPERATORS,
                                         INFIX_OPERATORS)
from clusto_query import clusto_types


SEARCH_KEYWORDS = list(clusto_types.CONTEXT_TYPES)[:]
SEARCH_KEYWORDS.extend(["name", "hostname", "role", "clusto_type"])

_single_quoted_string_re = re.compile(r"'(((\\')|[^'])*)'")
_double_quoted_string_re = re.compile(r'"(((\\")|[^"])*)"')
_unquoted_string_re = re.compile(r'([\w./:-]+)')
_separator_re = re.compile(r'[^a-zA-Z0-9_-]|\Z')


def consume(token, string):
    return string[len(token):]


def lex_string_inner(string):
    for char, regex in (("'", _single_quoted_string_re), ('"', _double_quoted_string_re)):
        if string.startswith(char):
            smd = regex.match(string)
            if not smd:
                raise StringParseError(string)
            return smd.group(1).replace('\\'+char, char), False, consume(smd.group(0), string)
    smd = _unquoted_string_re.match(string)
    if not smd:
        raise StringParseError(string)
    return smd.group(1), True, consume(smd.group(0), string)


SIZE_MAP = {
    'K': 1024,
    'M': 1024 * 1024,
    'G': 1024 * 1024 * 1024,
    'T': 1024 * 1024 * 1024 * 1024,
}


def convert_size(string):
    base = string[:-1]
    multiplier = SIZE_MAP[string[-1]]
    if all(c.isdigit() for c in base):
        base = int(base)
    else:
        base = float(base)
    return base * multiplier


def lex_string(string):
    parsed, maybe_is_number, rest = lex_string_inner(string)
    if maybe_is_number:
        if all(c.isdigit() or c == "." for c in parsed[:-1]) and parsed[-1] in SIZE_MAP:
            try:
                return convert_size(parsed), rest
            except Exception:
                return parsed, rest
        elif all(c.isdigit() for c in parsed):
            return int(parsed), rest
        elif all(c.isdigit() or c == "." for c in parsed):
            try:
                return float(parsed), rest
            except ValueError:
                return parsed, rest
    return parsed, rest


def lex(q):
    keywords = ["attr"]
    keywords.extend(SEARCH_KEYWORDS)
    keywords.extend(BOOLEAN_OPERATORS.keys())
    keywords.extend(UNARY_BOOLEAN_OPERATORS.keys())
    keywords.extend(INFIX_OPERATORS.keys())
    keywords.extend(("(", ")"))
    keywords.sort(key=len, reverse=True)
    results = []
    while q:
        q = q.lstrip()
        for keyword in keywords:
            if q.startswith(keyword):
                if _unquoted_string_re.match(keyword):
                    if not _separator_re.match(consume(keyword, q)):
                        continue
                results.append(keyword)
                q = consume(keyword, q)
                break
        else:
            result, q = lex_string(q)
            results.append(result)
    return results
