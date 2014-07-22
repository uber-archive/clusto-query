class QueryType(type):
    pass


class QueryObject(object):
    __metaclass__ = QueryType

    def run(self, candidate_hosts, context):
        return candidate_hosts
