import collections
import clusto


ContextKey = collections.namedtuple('ContextKey', ['item_type', 'name'])


def _generate_key(clusto_item):
    """ Generates a key for a clusto_item to be added to a context """
    return ContextKey(clusto_item._clusto_type, clusto_item.name)


class Context(object):
    """ Context for a clusto query. """
    CONTEXT_TYPES = ("pool", "datacenter")

    def __init__(self, clusto_proxy):
        self.clusto_proxy = clusto_proxy
        self.entity_map = dict((_generate_key(e), e)
                               for e in clusto_proxy.get_entities())
        self.context_dict = None

    @staticmethod
    def _populate_through_children(root, ctx):
        work_queue = [root]
        while work_queue:
            parent = work_queue.pop()
            for child in parent.contents():
                yield _generate_key(child), ctx
                work_queue.append(child)

    def populate_pools_and_datacenters(self):
        roots = self.clusto_proxy.get_entities(clusto_types=self.CONTEXT_TYPES)
        results = dict((typ, {}) for typ in self.CONTEXT_TYPES)
        for root in roots:
            if isinstance(root, clusto.drivers.Pool):
                typ = 'pool'
            elif isinstance(root,
                            clusto.drivers.datacenters.basicdatacenter.BasicDatacenter):
                typ = 'datacenter'
            for child, root in self._populate_through_children(root, _generate_key(root)):
                results[typ].setdefault(child, set([]))
                results[typ][child].add(root)
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
