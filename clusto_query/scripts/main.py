#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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

from __future__ import absolute_import
from __future__ import print_function

import itertools
import logging
import optparse
import os
import sys
import string

import clusto
import clusto.script_helper


from clusto_query.query.objects import RFC1918
from clusto_query.lexer import lex, SEARCH_KEYWORDS
from clusto_query.parser import parse_query
from clusto_query import settings
from clusto_query.context import Context
from clusto_query.query.operator.affix import Equality, Inequality
from clusto_query.query.operator.boolean import Intersection

__author__ = "James Brown <jbrown@uber.com>"
version_info = (0, 4, 0)
__version__ = ".".join(map(str, version_info))


long_help = """
clusto-query version %(version)s by %(author)s

Perform arbitrary boolean queries against clusto

Infix expression operators are the following:
    =   equality
    !=  inequality
    <=  le
    <   lt
    >   gt
    >=  ge
    ^   startswith
    ,   endswith
    contains  substring
    in_cidr ipv4 cidr comparisons

Additionally, there are boolean operators and, or, and - (set subtraction)

The following keywords can be directly queried:
%(search_keywords)s

Anything that's an "Attribute" must be prefixed with attr.

Here's an example query:

    clusto_type = server and
    (attr system.cpucount >= 15 or system.memory >= 32760)
    and datacenter = peak-mpl1'

This query fetches all servers with more than 16 cores or 32768 MB of RAM
located in the "peak-mlp1" datacenter. Neato!

Note that I put in "15" instead of "16" intentionally; clusto's cpu counting
is off-by-one. That was fun. Let's go again:

    clusto_type contains "server" and
    (attr nagios.disabled = 1 - hostname endswith peak2)

This one finds all servers that are disabled in nagios and do not have a
hostname that ends in peak2.

Quoting and parens work the way you expect them to.
""" % {
    'version': __version__,
    'author': __author__,
    'search_keywords': '\n'.join('- %s' % kw for kw in sorted(SEARCH_KEYWORDS))
}


log = None


class HostFormatter(object):
    option = None
    default = False

    def __init__(self, host, context):
        self.host = host
        self.context = context

    def name(self):
        return self.host.name

    def hostname(self):
        return self.host.hostname

    def role(self):
        return self.context.role_for_host(self.host)

    def internal_ips(self):
        return ",".join(ip for ip in self.host.get_ips() if ip in RFC1918)

    def public_ips(self):
        return ",".join(ip for ip in self.host.get_ips() if ip not in RFC1918)

    def rack(self):
        return ','.join(
            p.name for p
            in self.host.parents()
            if isinstance(p, clusto.drivers.racks.BasicRack)
        )

    def type(self):
        return self.host.type

    def __getitem__(self, item):
        if "." in item:
            key, subkey = item.split(".")
            return ",".join(map(str, (k.value for k in self.host.attrs(key=key, subkey=subkey))))
        return getattr(self, item)()


class EasierTemplate(string.Template):
    # $ is challenging in shell scripts
    delimiter = "%"
    idpattern = r'[a-z_][a-zA-Z0-9_.-]*'


def main():
    global log
    parser = optparse.OptionParser(usage="%prog [options] clusto_query_string", version=__version__)
    parser.add_option('-v', '--verbose', action='count', default=0)
    parser.add_option('-f', '--formatter', default=r"%name",
                      help='Formatter to use for printing, default "%default"')
    parser.add_option('--list-attributes', default=False, action='store_true',
                      help='Print all the queryable attributes')
    parser.add_option('--clusto-config', default='/etc/clusto/clusto.conf',
                      help='Path to clusto config file (default %default)')
    parser.add_option('--man', action="store_true", help="Show more detailed help")
    parser.add_option(
        '-m', '--merge-container-attrs', action='store_true',
        help="When showing attributes, merge in parents' attributes"
    )
    opts, args = parser.parse_args()

    level = logging.WARNING
    if opts.verbose == 1:
        level = logging.INFO
    elif opts.verbose > 1:
        level = logging.DEBUG

    if opts.man:
        print(long_help)
        return 0

    settings.merge_container_attrs = opts.merge_container_attrs

    conf = clusto.script_helper.load_config(opts.clusto_config)
    clusto.connect(conf)

    # clusto.connect screws up logging for all of its consumers, so we need
    # to init logging *after* calling clusto.connect
    log = logging.getLogger("clusto-query-logger")
    log.propagate = 0
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    handler.setLevel(level)
    log.addHandler(handler)
    log.setLevel(level)

    if opts.list_attributes:
        all_attrs = [it.attrs() for it in clusto.get_entities()]
        print("\n".join(sorted(set([".".join(map(str, (at.key, at.subkey)))
                                    for at in itertools.chain.from_iterable(all_attrs)]))))
        return 0

    if not args:
        parser.error("No query provided")
    raw_query = " ".join(args)

    log.info("Going to parse %r", raw_query)
    lexed_query = lex(raw_query)
    log.info("Lexed into %r", lexed_query)
    parsed_query, unparsed = parse_query(lexed_query)
    log.info("Parsed into %r", parsed_query)
    if unparsed:
        log.warning("Unparsed content: %r", unparsed)
        return 1

    if os.environ.get('CLUSTO_TYPE_FILTER', None) is not None:
        def look_for_type(node):
            if isinstance(node, (Equality, Inequality)) and\
                    ('type' in node.parameters or 'clusto_type' in node.parameters) and\
                    'server' in node.parameters:
                return True
            return False

        if not any(look_for_type(node) for node in parsed_query.visit_iter()):
            log.debug('Adding intersection with type=%s' % os.environ['CLUSTO_TYPE_FILTER'])
            parsed_query = Intersection(
                parsed_query,
                Equality('clusto_type', os.environ['CLUSTO_TYPE_FILTER'])
            )
            log.info('After intersection, parsed into %r', parsed_query)
        else:
            log.debug('Not adding type intersection')

    # fetch all the hosts
    format_template = EasierTemplate(opts.formatter)

    context = Context(clusto)
    for result_key in sorted(parsed_query.run(context.entity_map.keys(), context)):
        host = context.entity_map[result_key]
        print(format_template.substitute(HostFormatter(host, context)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
