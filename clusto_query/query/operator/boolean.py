from clusto_query.query.operator.base import Operator


BOOLEAN_OPERATORS = {}
UNARY_BOOLEAN_OPERATORS = {}


class BooleanOperator(Operator):
    operator_map = BOOLEAN_OPERATORS


class Intersection(BooleanOperator):
    operator = ("&", "and")

    def run(self, candidate_hosts, context):
        results = set(candidate_hosts)
        for p in self.parameters:
            results &= p.run(results, context)
        return results


class Union(BooleanOperator):
    operator = ("|", "or")

    def run(self, candidate_hosts, context):
        results = set()
        for p in self.parameters:
            results |= p.run(candidate_hosts, context)
        return results


class Subtraction(BooleanOperator):
    operator = "-"

    def run(self, candidate_hosts, context):
        results = self.parameters[0].run(candidate_hosts, context)
        for p in self.parameters[1:]:
            results -= p.run(candidate_hosts, context)
        return results


class UnaryBooleanOperator(Operator):
    operator_map = UNARY_BOOLEAN_OPERATORS


class Not(UnaryBooleanOperator):
    operator = ("not", "~")

    def run(self, candidate_hosts, context):
        return set(candidate_hosts) - self.parameters[0].run(candidate_hosts, context)
