import logging
import socket

from clusto_query.query.operator.base import Operator
from clusto_query.query.objects import Attribute, SimpleCidrSet


SUFFIX_OPERATORS = {}
INFIX_OPERATORS = {}
log = logging.getLogger("clusto-query-logger")


def flatten(list_of_lists):
    res = []
    for item in list_of_lists:
        if isinstance(item, (list, tuple)):
            res.extend(flatten(item))
        else:
            res.append(item)
    return res


def _extract_name_from_key(key):
    return key[1]


def _extract_property(host, attribute, context):
    if isinstance(attribute, Attribute):
        return flatten(attribute.get(host, context).values())
    if attribute == "clusto_type":
        return context.entity_map[host]._clusto_type
    elif attribute == "role":
        return context.role_for_host(host)
    elif attribute in context.context_types:
        return map(_extract_name_from_key, context.context(attribute, host))
    else:
        return getattr(context.entity_map[host], attribute)


class SuffixOperator(Operator):
    operator_map = SUFFIX_OPERATORS

    def __init__(self, lhs):
        self.lhs = lhs
        super(SuffixOperator, self).__init__(lhs)


class ExistsOperator(SuffixOperator):
    operator = ('exists',)

    def _exists(self, host, context):
        prop = _extract_property(host, self.lhs, context)
        return bool(prop)

    def run(self, candidate_hosts, context):
        hosts = set()
        for host in candidate_hosts:
            if self._exists(host, context):
                hosts.add(host)
        return hosts


class InfixOperator(Operator):
    operator_map = INFIX_OPERATORS
    satisfy_any_with_pool = True

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
        super(InfixOperator, self).__init__(lhs, rhs)

    def get_host_attribute(self, host, attribute, context):
        return _extract_property(host, attribute, context)

    def run(self, candidate_hosts, context):
        results = set()

        for host in candidate_hosts:
            log.debug("Checking %s for %s key %s and %s",
                      self.__class__.__name__, host, self.lhs, self.rhs)
            try:
                lhses = self.get_host_attribute(host, self.lhs, context)
            except AttributeError:
                continue
            match = False
            if not isinstance(lhses, (list, set, tuple)):
                lhses = [lhses]
            if (self.lhs == 'pool' or isinstance(self.lhs, Attribute)) and \
                    not self.satisfy_any_with_pool:
                log.debug('satisfying all')
                match = all(self.comparator(lhs, self.rhs) for lhs in lhses)
            else:
                match = any(self.comparator(lhs, self.rhs) for lhs in lhses)
            if match:
                log.debug("Check passed")
                results.add(host)
        return results

    @staticmethod
    def comparator(lhs, rhs):
        raise NotImplementedError()


class Equality(InfixOperator):
    operator = ("=", "is", "==")

    @staticmethod
    def comparator(lhs, rhs):
        if isinstance(lhs, Attribute):
            return lhs == rhs
        else:
            return str(lhs) == str(rhs)


class Inequality(InfixOperator):
    operator = ("!=", "isnt", "<>")
    # for inequalities, if we say (pool!=api), we want things that are not
    # in the API pool, not things that have a pool that is not API
    satisfy_any_with_pool = False

    @staticmethod
    def comparator(lhs, rhs):
        return lhs != rhs


class GT(InfixOperator):
    operator = ">"

    @staticmethod
    def comparator(lhs, rhs):
        return lhs > rhs


class GE(InfixOperator):
    operator = ">="

    @staticmethod
    def comparator(lhs, rhs):
        return lhs >= rhs


class LT(InfixOperator):
    operator = "<"

    @staticmethod
    def comparator(lhs, rhs):
        return lhs < rhs


class LE(InfixOperator):
    operator = "<="

    @staticmethod
    def comparator(lhs, rhs):
        return lhs <= rhs


class StartsWith(InfixOperator):
    operator = ("^", "startswith")

    @staticmethod
    def comparator(lhs, rhs):
        return lhs.startswith(rhs)


class EndsWith(InfixOperator):
    operator = (",", "endswith")

    @staticmethod
    def comparator(lhs, rhs):
        return lhs.endswith(rhs)


class SubString(InfixOperator):
    operator = "contains"

    @staticmethod
    def comparator(lhs, rhs):
        return rhs in lhs


class InCidr(InfixOperator):
    operator = "in_cidr"

    def __init__(self, lhs, rhs):
        super(InCidr, self).__init__(lhs, rhs)
        try:
            base, mask = rhs.split("/")
            base = socket.inet_ntoa(socket.inet_aton(base))  # check parse
            mask = int(mask)
            assert mask >= 0 and mask < 32
        except:
            raise ValueError("RHS must be a Cidr (base/mask)")

    @staticmethod
    def comparator(lhs, rhs):
        # TODO(jbrown): Support IPv6
        query = socket.inet_ntoa(socket.inet_aton(lhs))  # check parse
        cidr_set = SimpleCidrSet()
        base, mask = rhs.split("/")
        cidr_set.add_cidr(base, mask)
        return query in cidr_set
