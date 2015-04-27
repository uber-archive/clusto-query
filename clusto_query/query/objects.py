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

import socket
import struct

import clusto
from clusto_query.query import QueryObject
from clusto_query import settings


class SimpleCidrSet(object):
    def __init__(self):
        self.ranges = []

    def add_cidr(self, base, mask):
        """
        base: dotted-notation version of the base
        mask: integer for the netmask
        """
        mask = int(mask)
        base = struct.unpack('!L', socket.inet_aton(base))[0]
        maxsz = (01 << 32) - 1
        mask = 32 - mask
        mask = ((01 << mask) - 1) & maxsz
        min_addr = base & ~mask
        max_addr = base | mask
        self.ranges.append((min_addr, max_addr))

    def __contains__(self, address):
        """address should be dotted notation"""
        addr = struct.unpack('!L', socket.inet_aton(address))[0]
        for mina, maxa in self.ranges:
            if addr >= mina and addr <= maxa:
                return True
        return False

RFC1918 = SimpleCidrSet()
RFC1918.add_cidr('10.0.0.0', 8)
RFC1918.add_cidr('172.16.0.0', 12)
RFC1918.add_cidr('192.168.0.0', 16)


class Attribute(QueryObject):
    def __init__(self, key, subkey, number):
        self.key = key
        self.subkey = subkey
        self.number = int(number) if number is not None else None

    def __repr__(self):
        description = self.key
        if self.subkey:
            description += ".%s" % self.subkey
        if self.number:
            description += ":%d" % self.number
        return "Attribute(%s)" % description

    def get(self, host, context):
        kwargs = {
            'key': self.key,
            'merge_container_attrs': settings.merge_container_attrs
        }
        if self.subkey:
            kwargs['subkey'] = self.subkey
        if self.number is not None:
            kwargs['number'] = self.number
        resv = {}
        gotten = context.entity_map[host].attrs(**kwargs)
        for v in gotten:
            key = (v.key, v.subkey, v.number)
            if key in resv:
                resv[key].append(self._check(v.value))
            else:
                resv[key] = [self._check(v.value)]
        return resv

    @staticmethod
    def _check(value):
        # XXX: clusto.drivers.Pool inherits from basestring. why?
        if isinstance(value, clusto.drivers.base.driver.Driver):
            return value.name
        elif not isinstance(value, basestring):
            return value
        elif all(c.isdigit() for c in value):
            return int(value)
        elif all(c.isdigit() or c == "." for c in value):
            try:
                return float(value)
            except Exception:
                return value
        else:
            return value
