import socket
import struct

import clusto
from clusto_query.query import QueryObject


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
            if addr > mina and addr < maxa:
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
        kwargs = {'key': self.key, 'merge_container_attrs': True}
        if self.subkey:
            kwargs['subkey'] = self.subkey
        if self.number:
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
