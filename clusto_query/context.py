import collections
import clusto


ContextKey = collections.namedtuple('ContextKey', ['item_type', 'name'])


def _generate_key(clusto_item):
    """ Generates a key for a clusto_item to be added to a context """
    return ContextKey(clusto_item._clusto_type, clusto_item.name)


class Context(object):
    """ Context for a clusto query. """
    CONTEXT_TYPES = ("pool", "datacenter", "rack")

    def __init__(self, clusto_proxy):
        self.clusto_proxy = clusto_proxy
        self.entity_map = dict((_generate_key(e), e)
                               for e in clusto_proxy.get_entities())
        self.context_dict = None

    @staticmethod
    def str_type(clusto_object):
        if isinstance(clusto_object, clusto.drivers.Pool):
            return 'pool'
        elif isinstance(clusto_object,
                        clusto.drivers.basicdatacenter.BasicDatacenter):
            return 'datacenter'
        elif isinstance(clusto_object,
                        clusto.drivers.basicrack.BasicRack):
            return 'rack'
        else:
            return 'other'

    def populate_pools_and_datacenters(self):
        roots = self.clusto_proxy.get_entities(clusto_types=self.CONTEXT_TYPES)

        work_queue = roots[:]
        seen = set()

        forward_map = collections.defaultdict(set)

        types = {}

        # we're building a reverse map from (parent_type, object) to
        # parents. Remember that.
        #
        # unfortunately, this is just a DAG (not a tree or even an A-DAG),
        # so we can't just do a depth-first-search with path retention here
        # to build the map of parents. We'll do one pass against clusto to
        # build a shallow map of all parent-child relationships, then
        # flatten it to get transitive parent relationships, then reverse it.
        #
        # yay.
        while work_queue:
            root = work_queue.pop(0)
            if root in seen:
                continue
            seen.add(root)
            root_name = _generate_key(root)
            typ = self.str_type(root)
            types[root_name] = typ
            for child in root.contents():
                child_name = _generate_key(child)
                forward_map[root_name].add(child_name)
                if self.str_type(child) in self.CONTEXT_TYPES:
                    work_queue.append(child)

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
            typ = types[parent]
            for child in children:
                results[typ][child].add(parent)

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
