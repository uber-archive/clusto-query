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

import collections

from . import clusto_types

try:
    from clusto import adjacency_map
except:
    from .clusto_backport import adjacency_map


ContextKey = collections.namedtuple('ContextKey', ['item_type', 'name'])


def _generate_key(clusto_item):
    """ Generates a key for a clusto_item to be added to a context """
    return ContextKey(clusto_item._clusto_type, clusto_item.name)


class Context(object):
    """ Context for a clusto query. """
    CONTEXT_TYPES = clusto_types.CONTEXT_TYPES

    def __init__(self, clusto_proxy):
        self.clusto_proxy = clusto_proxy
        self.entity_map = dict((_generate_key(e), e)
                               for e in clusto_proxy.get_entities())
        self.context_dict = None

    @staticmethod
    def str_type(clusto_object):
        return getattr(clusto_object, 'type', 'other')

    def populate_pools_and_datacenters(self):
        seen = set()

        forward_map = collections.defaultdict(set)

        # we're building a reverse map from (parent_type, object) to
        # parents. Remember that.
        #
        # unfortunately, this is just a DG (not a tree or even an DAG),
        # so we can't just do a depth-first-search with path retention here
        # to build the map of parents. We'll do one pass against clusto to
        # build a shallow map of all parent-child relationships, then
        # flatten it to get transitive parent relationships, then reverse it.
        #
        # yay.
        relationships = adjacency_map()
        for row in relationships:
            if row.parent_type not in self.CONTEXT_TYPES:
                continue
            root_name = ContextKey(row.parent_type, row.parent_name)
            child_name = ContextKey(row.child_type, row.child_name)
            forward_map[root_name].add(child_name)

        # now flatten it
        transitive_contents = {}
        for pool_or_datacenter, contents in forward_map.iteritems():
            recursive_contents = set()
            seen = set()
            work_queue = list(contents)
            while work_queue:
                t = work_queue.pop(0)
                if t in seen:
                    continue
                seen.add(t)
                if t in forward_map:
                    work_queue.extend(forward_map[t])
                    recursive_contents.add(t)
                else:
                    recursive_contents.add(t)
            transitive_contents[pool_or_datacenter] = recursive_contents

        results = dict(
            (typ, collections.defaultdict(set))
            for typ
            in self.CONTEXT_TYPES
        )

        # finally, reverse it
        for parent, children in transitive_contents.iteritems():
            for child in children:
                results[parent.item_type][child].add(parent)

        self.context_dict = results

    def context(self, typ, host):
        if self.context_dict is None:
            self.populate_pools_and_datacenters()
        if typ in self.CONTEXT_TYPES:
            return self.context_dict[typ].get(host, set([]))
        else:
            raise AttributeError()

    def role_for_host(self, host):
        if not isinstance(host, ContextKey):
            host = _generate_key(host)
        for pool_key in self.context('pool', host):
            pool = self.entity_map[pool_key]
            maybe_attrs = pool.attrs(key='pooltype')
            if maybe_attrs and maybe_attrs[0].value == 'role':
                return pool.name
        return None
